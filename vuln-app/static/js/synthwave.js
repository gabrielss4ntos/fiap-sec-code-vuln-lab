// JavaScript para funcionalidades da aplicação vulnerável com tema synthwave
document.addEventListener('DOMContentLoaded', function() {
    // Criar linhas do sol synthwave
    createSunLines();
    
    // Inicializar botões de hint
    initHintButtons();
    
    // Inicializar sistema de flags
    initFlagSystem();
    
    // Efeito de digitação para terminal
    initTypewriterEffect();
});

// Função para criar as linhas do sol synthwave
function createSunLines() {
    const sunLines = document.querySelector('.sun-lines');
    if (!sunLines) return;
    
    const totalLines = 15;
    const halfHeight = 100;
    
    for (let i = 0; i < totalLines; i++) {
        const line = document.createElement('div');
        line.className = 'sun-line';
        const position = halfHeight + (i * 5);
        line.style.top = `${position}%`;
        line.style.opacity = 1 - (i / totalLines);
        sunLines.appendChild(line);
    }
}

// Inicializar botões de hint
function initHintButtons() {
    const hintButtons = document.querySelectorAll('.btn-hint');
    
    hintButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const hintId = this.getAttribute('data-hint');
            const hintBox = document.getElementById(hintId);
            
            if (hintBox) {
                if (hintBox.classList.contains('active')) {
                    hintBox.classList.remove('active');
                } else {
                    // Fechar outros hints abertos
                    document.querySelectorAll('.hint-box.active').forEach(box => {
                        box.classList.remove('active');
                    });
                    
                    hintBox.classList.add('active');
                }
            }
        });
    });
}

// Inicializar sistema de flags
function initFlagSystem() {
    const flagForms = document.querySelectorAll('.flag-form');
    
    flagForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const challengeId = this.getAttribute('data-challenge');
            const flagInput = this.querySelector('input[name="flag"]');
            const flagValue = flagInput.value.trim();
            
            // Verificar flag (normalmente seria feito via AJAX para o servidor)
            checkFlag(challengeId, flagValue, this);
        });
    });
}

// Verificar flag (simulação - em produção seria uma chamada AJAX)
function checkFlag(challengeId, flagValue, form) {
    // Mapeamento de desafios para flags (em produção, isso estaria no servidor)
    const flags = {
        'idor-challenge': 'FLAG{1D0R_4DM1N_4CC3SS}',
        'sqli-challenge': 'FLAG{SQL_1NJ3CT10N_M4ST3R}',
        'xss-challenge': 'FLAG{CR0SS_S1T3_SCR1PT1NG}',
        'bruteforce-challenge': 'FLAG{W34K_P4SSW0RD_P0L1CY}'
    };
    
    const resultElement = form.nextElementSibling;
    
    if (flags[challengeId] && flags[challengeId] === flagValue) {
        // Flag correta
        resultElement.className = 'alert alert-success';
        resultElement.textContent = 'Parabéns! Flag correta! Pontos adicionados ao seu perfil.';
        
        // Simular envio para CTFd (em produção seria uma chamada AJAX)
        console.log(`Flag correta para ${challengeId}: ${flagValue}`);
        
        // Atualizar UI para mostrar desafio completo
        const challengeCard = form.closest('.challenge-card');
        if (challengeCard) {
            challengeCard.classList.add('completed');
            
            // Atualizar contador de pontos (simulação)
            updatePoints(challengeId);
        }
    } else {
        // Flag incorreta
        resultElement.className = 'alert alert-danger';
        resultElement.textContent = 'Flag incorreta. Tente novamente.';
    }
    
    resultElement.style.display = 'block';
    
    // Esconder mensagem após 5 segundos
    setTimeout(() => {
        resultElement.style.display = 'none';
    }, 5000);
}

// Atualizar pontos do usuário (simulação)
function updatePoints(challengeId) {
    // Pontos por desafio (em produção, isso estaria no servidor)
    const points = {
        'idor-challenge': 100,
        'sqli-challenge': 200,
        'xss-challenge': 150,
        'bruteforce-challenge': 100
    };
    
    const pointsElement = document.getElementById('user-points');
    if (pointsElement) {
        const currentPoints = parseInt(pointsElement.textContent) || 0;
        const newPoints = currentPoints + (points[challengeId] || 0);
        pointsElement.textContent = newPoints;
        
        // Animação de pontos
        pointsElement.classList.add('points-updated');
        setTimeout(() => {
            pointsElement.classList.remove('points-updated');
        }, 1000);
    }
}

// Efeito de digitação para terminal
function initTypewriterEffect() {
    const elements = document.querySelectorAll('.typewriter');
    
    elements.forEach(element => {
        const text = element.textContent;
        const speed = parseInt(element.getAttribute('data-speed')) || 50;
        
        element.textContent = '';
        let i = 0;
        
        function typeWriter() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, speed);
            } else {
                // Adicionar cursor piscante ao final
                const cursor = document.createElement('span');
                cursor.className = 'blink';
                cursor.textContent = '█';
                element.appendChild(cursor);
            }
        }
        
        typeWriter();
    });
}

// Função para registro de usuário
function registerUser(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const email = document.getElementById('email').value;
    
    // Validação básica
    if (!username || !password) {
        showAlert('Preencha todos os campos obrigatórios', 'danger');
        return;
    }
    
    // Em produção, isso seria uma chamada AJAX para o servidor
    // Simulação de registro bem-sucedido
    const userId = generateUserId();
    
    // Mostrar ID do usuário (vulnerabilidade IDOR)
    showAlert(`Registro bem-sucedido! Seu ID de usuário é: ${userId}`, 'success');
    
    // Redirecionar para dashboard após 3 segundos
    setTimeout(() => {
        window.location.href = '/dashboard';
    }, 3000);
}

// Gerar ID de usuário (simulação)
function generateUserId() {
    // Em produção, isso seria gerado pelo servidor
    // Para fins de demonstração, geramos um ID sequencial
    return Math.floor(10 + Math.random() * 90);
}

// Mostrar alerta
function showAlert(message, type) {
    const alertBox = document.createElement('div');
    alertBox.className = `alert alert-${type}`;
    alertBox.textContent = message;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertBox, container.firstChild);
    
    // Remover alerta após 5 segundos
    setTimeout(() => {
        alertBox.remove();
    }, 5000);
}

// Função para login
function loginUser(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    // Validação básica
    if (!username || !password) {
        showAlert('Preencha todos os campos', 'danger');
        return;
    }
    
    // Credenciais vulneráveis para demonstração
    if (username === 'admin' && password === 'admin123') {
        // Login como admin
        window.location.href = '/admin-dashboard';
    } else {
        // Simulação de login normal
        window.location.href = '/dashboard';
    }
}

// Função para exibir painel de admin (vulnerabilidade IDOR)
function viewAdminPanel(userId) {
    // Em produção, isso verificaria permissões no servidor
    // Vulnerabilidade IDOR: qualquer ID pode ser passado
    fetch(`/api/user/${userId}/profile`)
        .then(response => response.json())
        .then(data => {
            if (data.is_admin) {
                window.location.href = '/admin-panel';
            } else {
                showAlert('Acesso negado', 'danger');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            showAlert('Erro ao acessar perfil', 'danger');
        });
}
