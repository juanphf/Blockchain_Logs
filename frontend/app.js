// frontend/app.js

// Estado Global
let mempoolLogs = [];
let maxMempool = 10;
let connectionActive = false;

// Referências da DOM
const mempoolContainer = document.getElementById('mempool-container');
const blocksContainer = document.getElementById('blocks-container');
const mempoolCount = document.getElementById('mempool-count');
const latestBlockIndex = document.getElementById('latest-block-index');
const connectionIndicator = document.getElementById('connection-status');
const nodeCountVal = document.getElementById('node-count-val');

// Construir o HTML de um Card Log
function createLogElement(log) {
    const div = document.createElement('div');
    div.className = `log-item level-${log.level}`;
    if (log.is_invalid) div.classList.add('invalid-log');

    div.innerHTML = `
        <div class="log-top">
            <span class="log-level">${log.level} ${log.is_invalid ? '<span style="color: #ef4444; font-weight: 800; font-size: 0.65rem; margin-left: 5px;">[ATAQUE BLOQUEADO]</span>' : ''}</span>
            <span class="log-pod">${log.namespace} / ${log.pod_name}</span>
        </div>
        <div class="log-msg">"${log.message}"</div>
        <div class="log-sig">Sig: ${log.signature ? log.signature.substring(0, 30) + '...' : 'INVALID'}</div>
    `;
    return div;
}

// Renderizar a mempool array na tela
function renderMempool() {
    mempoolContainer.innerHTML = '';
    // Vamos inverter o array para que o log que acabou de entrar seja o primeiro a ser desenhado no topo da tela
    const reversedLogs = [...mempoolLogs].reverse();
    let validCount = 0;
    
    reversedLogs.forEach(log => {
        if (!log.is_invalid) validCount++;
        mempoolContainer.appendChild(createLogElement(log));
    });
    
    mempoolCount.innerText = `${validCount}/${maxMempool}`;
}

// Renderizar um bloco solitário na tela do Blockchain
function prependBlockToChain(block, isFirst = false) {
    const wrapper = document.createElement('div');
    wrapper.className = 'block-wrapper';

    // Se não for o primeirissimo (Genesis base da tela), coloca o conector caindo nele
    const connectorHTML = isFirst ? '' : '<div class="block-connector"></div>';

    // Opcional truncar os hashes na visualizacao para nao quebrar a tela inteira
    const hash = block.hash || 'Vazio (Sendo selado...)';

    // O conector HTML é posicionado DEPOIS do card para simular o elo descendo até o bloco antigo que está embaixo dele na tela.
    wrapper.innerHTML = `
        <div class="block-card">
            <div class="block-header">
                <span class="block-index">BLOCO #${block.index}</span>
                <span class="badge success">✔️ 10 Logs</span>
            </div>
            
            <div class="block-hash-box">
                <div class="hash-label">Hash SHA-256 (Imutável)</div>
                <div class="hash-val">${hash}</div>
            </div>
            
            <div class="block-hash-box" style="background: rgba(0,0,0,0.15);">
                <div class="hash-label">Hash Anterior (Corrente)</div>
                <div class="hash-val prev">${block.previous_hash}</div>
            </div>
            
            <div class="block-footer">
                <span>Timestamp: ${new Date(block.timestamp * 1000).toLocaleString('pt-BR')}</span>
            </div>
        </div>
        ${connectorHTML}
    `;

    // Insere no topo da corrente visual (o bloco mais recente cai em cima)
    blocksContainer.prepend(wrapper);
    latestBlockIndex.innerText = block.index;
}

// Iniciar Conexão WebSocket
function connectWebSocket() {
    console.log("Conectando ao nó Blockchain...");
    const socket = new WebSocket('ws://localhost:5000/ws');

    socket.onopen = (e) => {
        console.log("Conectado ao Websocket!");
        connectionActive = true;
        connectionIndicator.classList.remove('disconnected');
    };

    socket.onmessage = (event) => {
        const payload = JSON.parse(event.data);

        if (payload.type === "CHAIN_HISTORY") {
            // Histórico recebido na primeira carga
            const chain = payload.data;
            blocksContainer.innerHTML = ''; // zera
            // Renderiza historico. Array vem do zero ao mais recente.
            // Para o visual ficar "caindo de cima pra baixo", passamos a lista.
            chain.forEach((block, idx) => {
                prependBlockToChain(block, idx === 0);
            });

        } else if (payload.type === "NEW_LOG") {
            // Novo Log entrou na sala de espera
            mempoolLogs.push(payload.data);
            renderMempool();
            
        } else if (payload.type === "NODE_COUNT") {
            // Heartbeat recebido contabilizou nós ativos
            nodeCountVal.innerText = payload.data;

        } else if (payload.type === "NEW_BLOCK") {
            // Capacidade máxima bateu e o servidor fechou o hash
            prependBlockToChain(payload.data, blocksContainer.children.length === 0);
            // Limpa os logs que já subiram para o bloco principal da tela esquerda
            mempoolLogs = [];
            renderMempool();
        }
    };

    socket.onclose = () => {
        console.log("Conexão perdida. Tentando reconectar...");
        connectionActive = false;
        connectionIndicator.classList.add('disconnected');
        setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = (err) => {
        console.error("Websocket Erro: ", err);
    }
}

// Inicializa a aplicação
connectWebSocket();
