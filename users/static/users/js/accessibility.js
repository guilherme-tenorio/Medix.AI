(() => {
    const toolbar = document.querySelector('[data-accessibility-toolbar]');
    const status = document.querySelector('[data-accessibility-status]');
    if (!toolbar || !status) return;

    const storageKey = 'medix-accessibility-preferences';
    const textSizes = new Set(['smaller', 'normal', 'larger']);
    let preferences = { textSize: 'normal', highContrast: false };

    try {
        const stored = JSON.parse(window.localStorage.getItem(storageKey) || '{}');
        if (textSizes.has(stored.textSize)) preferences.textSize = stored.textSize;
        preferences.highContrast = stored.highContrast === true;
    } catch {
        // Preferências continuam disponíveis durante a sessão se o armazenamento estiver bloqueado.
    }

    const announce = (message) => {
        status.textContent = '';
        window.requestAnimationFrame(() => {
            status.textContent = message;
        });
    };

    const savePreferences = () => {
        try {
            window.localStorage.setItem(storageKey, JSON.stringify(preferences));
        } catch {
            // A mudança visual permanece aplicada mesmo sem persistência local.
        }
    };

    const applyPreferences = () => {
        document.documentElement.dataset.textSize = preferences.textSize;
        document.documentElement.dataset.highContrast = String(preferences.highContrast);
        toolbar.querySelector('[data-contrast-toggle]')?.setAttribute(
            'aria-pressed',
            String(preferences.highContrast),
        );
    };

    toolbar.hidden = false;
    applyPreferences();

    toolbar.addEventListener('click', (event) => {
        const button = event.target.closest('button');
        if (!button) return;

        if (button.matches('[data-text-size]')) {
            preferences.textSize = button.dataset.textSize;
            applyPreferences();
            savePreferences();
            const labels = {
                smaller: 'Texto reduzido.',
                normal: 'Tamanho padrão do texto restaurado.',
                larger: 'Texto ampliado.',
            };
            announce(labels[preferences.textSize]);
            return;
        }

        if (button.matches('[data-contrast-toggle]')) {
            preferences.highContrast = !preferences.highContrast;
            applyPreferences();
            savePreferences();
            announce(preferences.highContrast ? 'Alto contraste ativado.' : 'Alto contraste desativado.');
            return;
        }

    });
})();
