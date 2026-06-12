const activeControllers = new Map();
const LOCAL_BACKEND = 'http://localhost:8000';
const LOOPBACK_BACKEND = 'http://127.0.0.1:8000';
const COMPARE_STREAM_TIMEOUT_MS = 900000;

function fallbackBackendEndpoint(endpoint) {
    if (endpoint.startsWith(LOCAL_BACKEND)) {
        return endpoint.replace(LOCAL_BACKEND, LOOPBACK_BACKEND);
    }
    if (endpoint.startsWith(LOOPBACK_BACKEND)) {
        return endpoint.replace(LOOPBACK_BACKEND, LOCAL_BACKEND);
    }
    return '';
}

function fetchBackend(endpoint, options) {
    return fetch(endpoint, options).catch((error) => {
        const fallback = fallbackBackendEndpoint(endpoint);
        if (!fallback || error.name === 'AbortError' || options?.signal?.aborted) {
            throw error;
        }
        return fetch(fallback, options);
    });
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    const endpointByAction = {
        fetchHealth: `${LOCAL_BACKEND}/`,
        fetchOllamaModels: `${LOCAL_BACKEND}/ollama-models`,
        fetchStarterQuestions: `${LOCAL_BACKEND}/starter-questions`,
        fetchCacheStatus: `${LOCAL_BACKEND}/cache-status`,
        fetchIndex: `${LOCAL_BACKEND}/index`,
        fetchChat: `${LOCAL_BACKEND}/chat`,
        fetchChatStream: `${LOCAL_BACKEND}/chat/stream`,
        fetchCompare: `${LOCAL_BACKEND}/compare`,
        fetchCompareStream: `${LOCAL_BACKEND}/compare/stream`,
        fetchCancel: `${LOCAL_BACKEND}/cancel`,
        fetchFeedback: `${LOCAL_BACKEND}/feedback`,
        fetchPageSummary: `${LOCAL_BACKEND}/summarize-page`,
        fetchFlowchart: `${LOCAL_BACKEND}/flowchart`,
        fetchChart: `${LOCAL_BACKEND}/chart`,
        fetchDocumentUpload: `${LOCAL_BACKEND}/document/upload`,
        fetchCrawl: `${LOCAL_BACKEND}/crawl`,
        fetchSafety: `${LOCAL_BACKEND}/safety-check`,
        fetchWebpageContent: `${LOCAL_BACKEND}/webpage-content`,
    };

    if (request.action === 'abortRequest') {
        const requestId = request.requestId || request.payload?.request_id;
        const controller = activeControllers.get(requestId);
        if (controller) {
            controller.abort();
            activeControllers.delete(requestId);
        }
        sendResponse({ aborted: Boolean(controller), request_id: requestId });
        return false;
    }

    if (request.action === 'fetchChatStream' || request.action === 'fetchCompareStream') {
        const isCompareStream = request.action === 'fetchCompareStream';
        const endpoint = isCompareStream ? endpointByAction.fetchCompareStream : endpointByAction.fetchChatStream;
        const controller = new AbortController();
        const requestId = request.requestId || request.payload?.request_id || '';
        if (requestId) {
            activeControllers.set(requestId, controller);
        }

        let timeoutFired = false;
        const timeoutId = setTimeout(() => {
            timeoutFired = true;
            controller.abort();
        }, isCompareStream ? COMPARE_STREAM_TIMEOUT_MS : 300000);
        let sawStreamTerminalEvent = false;
        let sawStreamDelta = false;
        const sendStreamEvent = (event) => {
            if (sender.tab?.id) {
                chrome.tabs.sendMessage(sender.tab.id, {
                    action: isCompareStream ? 'compareStreamEvent' : 'chatStreamEvent',
                    requestId,
                    event
                });
            }

            if (event && typeof event.type === 'string') {
                if (event.type === 'delta' && event.text) {
                    sawStreamDelta = true;
                }
                if (['done', 'compare_done', 'error', 'external_required'].includes(event.type)) {
                    sawStreamTerminalEvent = true;
                }
            }
        };

        sendResponse({ ok: true, streaming: true });

        // Delay by one tick so content.js listener is registered before first events fire
        Promise.resolve().then(() => fetchBackend(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request.payload),
            signal: controller.signal
        })
        .then(async (response) => {
            if (!response.ok) {
                let detail = 'Backend stream error';
                try {
                    const err = await response.json();
                    detail = err.detail || detail;
                } catch (_) {}
                throw new Error(detail);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed) continue;
                    try {
                        sendStreamEvent(JSON.parse(trimmed));
                    } catch (error) {
                        console.warn('Invalid stream event:', trimmed, error);
                    }
                }
            }

            const trailing = buffer.trim();
            if (trailing) {
                try {
                    sendStreamEvent(JSON.parse(trailing));
                } catch (error) {
                    console.warn('Invalid trailing stream event:', trailing, error);
                }
            }

            if (!sawStreamTerminalEvent && !controller.signal.aborted) {
                sendStreamEvent(isCompareStream
                    ? { type: 'error', message: 'Compare is taking longer than expected. Local Ollama models can be slow on large sources. The structured comparison may still be available.' }
                    : (sawStreamDelta
                        ? { type: 'done', provider: '', model: '', suggestions: [] }
                        : { type: 'error', message: 'Streaming response closed before completion.' })
                );
            }
        })
        .catch((error) => {
            const message = error.name === 'AbortError'
                ? (timeoutFired && isCompareStream
                    ? 'Compare is taking longer than expected. Local Ollama models can be slow on large sources. The structured comparison may still be available.'
                    : 'Request cancelled.')
                : error.toString();
            sendStreamEvent({ type: 'error', message });
        })
        .finally(() => {
            clearTimeout(timeoutId);
            if (requestId) {
                activeControllers.delete(requestId);
            }
        }));

        return true;
    }

    const endpoint = endpointByAction[request.action];
    if (endpoint) {
        const controller = new AbortController();
        const requestId = request.requestId || request.payload?.request_id || '';
        if (requestId && request.action !== 'fetchCancel') {
            activeControllers.set(requestId, controller);
        }
        const timeoutByAction = {
            fetchCacheStatus: 60000,
            fetchIndex: 180000,
            fetchChat: 300000,
            fetchCompare: COMPARE_STREAM_TIMEOUT_MS,
            fetchPageSummary: 180000,
            fetchFlowchart: 420000,
            fetchChart: 300000,
            fetchDocumentUpload: 180000,
            fetchCrawl: 300000,
            fetchSafety: 10000,
            fetchCancel: 10000,
            fetchWebpageContent: 20000,
        };
        const timeoutMs = timeoutByAction[request.action] || 45000;
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

        fetchBackend(endpoint, {
            method: ['fetchHealth', 'fetchOllamaModels'].includes(request.action) ? 'GET' : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: ['fetchHealth', 'fetchOllamaModels'].includes(request.action) ? undefined : JSON.stringify(request.payload),
            signal: controller.signal
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.detail || 'Backend error') });
            }
            return response.json();
        })
        .then(data => sendResponse(data))
        .catch(error => {
            if (request.action === 'fetchSafety') {
                console.debug("Background safety check skipped:", error);
            } else {
                console.error("Background Fetch Error:", error);
            }
            const timeoutMessageByAction = {
                fetchCacheStatus: 'Backend cache check timed out.',
                fetchIndex: 'Page indexing timed out. Large pages or first-time embedding model load can take longer.',
                fetchChat: 'Backend chat request timed out. The local Ollama fallback may still be generating.',
                fetchCompare: 'Compare Tool timed out. Try shorter sources or another model.',
                fetchPageSummary: 'Page summarizer timed out. Try a shorter summary or another model.',
                fetchFlowchart: 'Flowchart tool timed out. Try an overview flowchart or another model.',
                fetchChart: 'Chart tool timed out. Try a simpler chart or another model.',
                fetchDocumentUpload: 'Document upload timed out.',
                fetchCrawl: 'Website crawl timed out.',
                fetchSafety: 'Safety check timed out.',
                fetchCancel: 'Cancel request timed out.'
            };
            const message = error.name === 'AbortError'
                ? (request.action === 'fetchChat' ? 'Request cancelled.' : timeoutMessageByAction[request.action] || 'Backend request timed out. Please check that the backend and model are running.')
                : error.toString();
            sendResponse({ error: message });
        })
        .finally(() => {
            clearTimeout(timeoutId);
            if (requestId && request.action !== 'fetchCancel') {
                activeControllers.delete(requestId);
            }
        });
        
        return true; // Keep the message channel open for async response
    }
});
