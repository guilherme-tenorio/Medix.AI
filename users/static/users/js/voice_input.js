(() => {
    const status = document.querySelector('[data-accessibility-status]');
    const voiceToggle = document.querySelector('[data-voice-toggle]');
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    let activeRecognition = null;
    let voiceEnabled = false;

    const announce = (message) => {
        if (!status) return;
        status.textContent = '';
        window.requestAnimationFrame(() => {
            status.textContent = message;
        });
    };

    const speakText = (text) => {
        if (!('speechSynthesis' in window) || !text) {
            announce('Leitura em áudio indisponível neste navegador.');
            return;
        }
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'pt-BR';
        utterance.rate = 0.92;
        window.speechSynthesis.speak(utterance);
        announce('Reproduzindo orientação por áudio.');
    };

    const stopRecognition = () => {
        if (activeRecognition) {
            try {
                activeRecognition.stop();
            } catch {
                // Ignora erro se reconhecimento já foi encerrado.
            }
            activeRecognition = null;
        }
    };

    const setVoiceMode = (enabled) => {
        voiceEnabled = enabled;
        if (voiceToggle) {
            voiceToggle.setAttribute('aria-pressed', String(enabled));
            voiceToggle.textContent = enabled ? 'Modo voz ativo' : 'Ativar voz';
        }
        document.querySelectorAll('[data-voice-target]').forEach((btn) => {
            btn.hidden = !enabled;
        });
        if (!enabled) {
            stopRecognition();
        }
        announce(
            enabled
                ? 'Modo de voz ativado. Você pode alternar para digitação a qualquer momento.'
                : 'Modo de voz desativado. Digitação disponível.',
        );
    };

    if (voiceToggle) {
        voiceToggle.hidden = false;
        voiceToggle.addEventListener('click', () => {
            setVoiceMode(!voiceEnabled);
        });
    }

    document.addEventListener('click', (event) => {
        const ttsButton = event.target.closest('[data-tts-source]');
        if (ttsButton) {
            const target = document.querySelector(ttsButton.dataset.ttsSource);
            const text = ttsButton.dataset.ttsText || (target ? target.textContent.trim() : '');
            speakText(text);
            return;
        }

        const voiceFieldBtn = event.target.closest('[data-voice-target]');
        if (!voiceFieldBtn) return;

        const input = document.querySelector(voiceFieldBtn.dataset.voiceTarget);
        if (!input) return;

        if (!SpeechRecognition) {
            announce('Reconhecimento de voz não suportado neste navegador. Continue digitando.');
            input.focus();
            return;
        }

        stopRecognition();
        const recognition = new SpeechRecognition();
        recognition.lang = 'pt-BR';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        activeRecognition = recognition;

        recognition.onresult = (recEvent) => {
            const result = recEvent.results[0] && recEvent.results[0][0];
            if (!result) return;
            const transcript = result.transcript.trim();
            const confidence = typeof result.confidence === 'number' ? result.confidence : 1;
            input.value = transcript;
            input.dispatchEvent(new Event('input', { bubbles: true }));
            if (confidence < 0.75) {
                announce(`Transcrição com baixa confiança (${Math.round(confidence * 100)}%). Revise o texto: ${transcript}`);
            } else {
                announce('Transcrição concluída e inserida no campo.');
            }
        };

        recognition.onerror = (errEvent) => {
            if (errEvent.error === 'not-allowed' || errEvent.error === 'service-not-allowed') {
                announce('Permissão de microfone negada. Continue digitando normalmente.');
            } else {
                announce('Não foi possível capturar a fala. Continue digitando.');
            }
            input.focus();
        };

        recognition.onend = () => {
            activeRecognition = null;
        };

        try {
            recognition.start();
            announce('Ouvindo em português. Fale agora.');
        } catch {
            announce('Microfone indisponível. Continue digitando.');
        }
    });
})();
