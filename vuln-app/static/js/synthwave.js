// JavaScript para funcionalidades da aplicação vulnerável com tema synthwave

// Função para efeito de digitação
document.addEventListener('DOMContentLoaded', function() {
    const typewriterElements = document.querySelectorAll('.typewriter');
    
    typewriterElements.forEach(element => {
        const text = element.textContent;
        const speed = parseInt(element.getAttribute('data-speed')) || 100;
        
        element.textContent = '';
        let i = 0;
        
        function typeWriter() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, speed);
            }
        }
        
        typeWriter();
    });
    
    // Configurar os botões de hint
    const hintButtons = document.querySelectorAll('.btn-hint');
    hintButtons.forEach(button => {
        button.addEventListener('click', function() {
            const hintId = this.getAttribute('data-hint');
            const hintBox = document.getElementById(hintId);
            
            if (hintBox.style.display === 'block') {
                hintBox.style.display = 'none';
            } else {
                hintBox.style.display = 'block';
            }
        });
    });
    
    // Configurar os formulários de submissão de flag
    const flagForms = document.querySelectorAll('.flag-form');
    flagForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const challengeId = this.getAttribute('data-challenge');
            const flagInput = this.querySelector('input[name="flag"]');
            const flag = flagInput.value.trim();
            const alertBox = this.nextElementSibling;
            
            if (!flag) {
                showAlert(alertBox, 'Por favor, insira uma flag.', 'error');
                return;
            }
            
            // Enviar a flag para o servidor
            fetch('/api/submit_flag', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `challenge_id=${challengeId}&flag=${encodeURIComponent(flag)}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert(alertBox, data.message, 'success');
                    // Atualizar pontuação após alguns segundos
                    setTimeout(() => {
                        location.reload();
                    }, 2000);
                } else {
                    showAlert(alertBox, data.message, 'error');
                }
            })
            .catch(error => {
                showAlert(alertBox, 'Erro ao enviar flag. Tente novamente.', 'error');
                console.error('Error:', error);
            });
        });
    });
    
    // Função para mostrar alertas
    function showAlert(element, message, type) {
        element.textContent = message;
        element.style.display = 'block';
        
        if (type === 'success') {
            element.className = 'alert alert-success';
        } else {
            element.className = 'alert alert-error';
        }
        
        // Esconder o alerta após 5 segundos
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
    
    // Função para registrar usuário
    window.registerUser = function(event) {
        event.preventDefault();
        
        const username = document.getElementById('username').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        
        if (!username || !email || !password) {
            alert('Por favor, preencha todos os campos obrigatórios.');
            return;
        }
        
        if (password !== confirmPassword) {
            alert('As senhas não coincidem.');
            return;
        }
        
        // Enviar dados para o servidor
        const formData = new FormData();
        formData.append('username', username);
        formData.append('email', email);
        formData.append('password', password);
        
        fetch('/register', {
            method: 'POST',
            body: formData
        })
        .then(response => response.text())
        .then(html => {
            // Substituir o conteúdo da página com a resposta
            document.open();
            document.write(html);
            document.close();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Erro ao registrar. Tente novamente.');
        });
    };
});
