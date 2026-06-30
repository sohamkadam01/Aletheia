let activeStreams = new Map();
const activeControllers = new Map();

chrome.storage.session.get("activeStreams", (data) => {
    if (data?.activeStreams) {
        activeStreams = new Map(data.activeStreams);
    }
});

function saveActiveStreams() {
    const serializable = Array.from(activeStreams.entries()).map(([id, stream]) => [
        id,
        { ...stream, controller: null }
    ]);
    chrome.storage.session.set({ activeStreams: serializable });
}

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
        fetchWorkflowDiscovery: `${LOCAL_BACKEND}/workflow-discovery`,
        fetchFlowchart: `${LOCAL_BACKEND}/flowchart`,
        fetchChart: `${LOCAL_BACKEND}/chart`,
        fetchDocumentUpload: `${LOCAL_BACKEND}/document/upload`,
        fetchCrawl: `${LOCAL_BACKEND}/crawl`,
        fetchSafety: `${LOCAL_BACKEND}/safety-check`,
        fetchWebpageContent: `${LOCAL_BACKEND}/webpage-content`,
        fetchUrlDocument: `${LOCAL_BACKEND}/fetch-url-document`,
        fetchSearchConfig: `${LOCAL_BACKEND}/search-config`,
        fetchIntentRoute: `${LOCAL_BACKEND}/intent-route`,
    };

    if (request.action === 'abortRequest') {
        const requestId = request.requestId || request.payload?.request_id;
        let aborted = false;
        
        const stream = activeStreams.get(requestId);
        if (stream) {
            if (stream.controller) stream.controller.abort();
            stream.status = "aborted";
            stream.updatedAt = Date.now();
            saveActiveStreams();
            aborted = true;
        }

        const controller = activeControllers.get(requestId);
        if (controller) {
            controller.abort();
            activeControllers.delete(requestId);
            aborted = true;
        }

        sendResponse({ aborted, request_id: requestId });
        return false;
    }

    if (request.action === 'reconnectStream') {
        const url = request.url;
        let foundStream = null;
        for (const [id, stream] of activeStreams.entries()) {
            if (stream.url === url && stream.status !== 'aborted') {
                foundStream = stream;
            }
        }
        if (foundStream) {
            // Update tabId to new tab
            foundStream.tabId = sender.tab?.id;
            sendResponse({
                active: true,
                requestId: foundStream.requestId,
                partialContent: foundStream.partialContent,
                sources: foundStream.sources,
                status: foundStream.status,
                isCompare: foundStream.isCompare
            });
        } else {
            sendResponse({ active: false });
        }
        return false;
    }

    if (request.action === 'fetchChatStream' || request.action === 'fetchCompareStream') {
        const isCompareStream = request.action === 'fetchCompareStream';
        const endpoint = isCompareStream ? endpointByAction.fetchCompareStream : endpointByAction.fetchChatStream;
        const controller = new AbortController();
        const requestId = request.requestId || request.payload?.request_id || '';
        
        let stream = {
            requestId,
            tabId: sender.tab?.id,
            url: request.payload?.url || '',
            isCompare: isCompareStream,
            controller,
            partialContent: "",
            sources: [],
            status: "active",
            createdAt: Date.now(),
            updatedAt: Date.now()
        };
        
        if (requestId) {
            activeStreams.set(requestId, stream);
            saveActiveStreams();
        }

        let timeoutFired = false;
        const timeoutId = setTimeout(() => {
            timeoutFired = true;
            controller.abort();
        }, isCompareStream ? COMPARE_STREAM_TIMEOUT_MS : 300000);
        let sawStreamTerminalEvent = false;
        let sawStreamDelta = false;
        const sendStreamEvent = (event) => {
            if (event && typeof event.type === 'string') {
                if (event.type === 'delta' && event.text) {
                    sawStreamDelta = true;
                    stream.partialContent += event.text;
                } else if (event.type === 'compare_result') {
                    stream.partialContent += (event.result?.answer || '');
                    stream.sources = event.sources || [];
                } else if (event.type === 'meta') {
                    if (event.sources) stream.sources = event.sources;
                }
                
                stream.updatedAt = Date.now();
                saveActiveStreams();
                
                if (['done', 'compare_done', 'error', 'external_required'].includes(event.type)) {
                    sawStreamTerminalEvent = true;
                    if (event.type === 'error' || event.type === 'external_required') {
                        stream.status = "error";
                    } else {
                        stream.status = "completed";
                    }
                    saveActiveStreams();
                    
                    // Cleanup memory after 15 minutes
                    setTimeout(() => {
                        activeStreams.delete(requestId);
                        saveActiveStreams();
                    }, 15 * 60 * 1000);
                }
            }

            if (stream.tabId) {
                chrome.tabs.sendMessage(stream.tabId, {
                    action: isCompareStream ? 'compareStreamEvent' : 'chatStreamEvent',
                    requestId,
                    event
                }, () => {
                    // The tab may have navigated or closed while a stream is active.
                    // Reading lastError prevents Chrome from surfacing a noisy runtime error.
                    void chrome.runtime.lastError;
                });
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
            // activeStreams cleanup is handled internally via timeout in sendStreamEvent
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
            fetchWorkflowDiscovery: 720000,
            fetchFlowchart: 420000,
            fetchChart: 300000,
            fetchDocumentUpload: 180000,
            fetchCrawl: 300000,
            fetchSafety: 10000,
            fetchCancel: 10000,
            fetchWebpageContent: 20000,
            fetchUrlDocument: 30000,
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
                fetchWorkflowDiscovery: 'Workflow Discovery timed out. Try lowering the crawl limit or another model.',
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
