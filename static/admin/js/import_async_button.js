// Script pour ajouter le bouton d'import asynchrone dans la page des produits
(function() {
    'use strict';
    
    function addImportButton() {
        // Vérifier si on est sur la page des produits
        const currentPath = window.location.pathname;
        if (!currentPath.includes('/admin/masterdata/product')) {
            return;
        }
        
        // Chercher object-tools (où sont les boutons Import/Export/Ajouter)
        const objectTools = document.querySelector('ul.object-tools');
        
        if (objectTools) {
            // Vérifier si le bouton existe déjà
            const importUrl = '/admin/masterdata/product/import-async/';
            const existingBtn = objectTools.querySelector('a[href="' + importUrl + '"]');
            if (existingBtn) {
                return; // Bouton déjà présent
            }
            
            // Créer le bouton dans un <li> (format standard Django admin)
            const li = document.createElement('li');
            const importBtn = document.createElement('a');
            importBtn.href = importUrl;
            importBtn.className = 'import-async-button-modern';
            importBtn.innerHTML = '<i class="fas fa-cloud-upload-alt btn-icon"></i><span class="btn-text">Import asynchrone</span>';
            
            // Ajouter les styles modernes avec Font Awesome
            if (!document.querySelector('link[href*="font-awesome"]')) {
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css';
                document.head.appendChild(link);
            }
            
            const style = document.createElement('style');
            style.textContent = `
                .import-async-button-modern {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                    color: white !important;
                    padding: 11px 22px !important;
                    border-radius: 10px !important;
                    font-weight: 600 !important;
                    font-size: 13px !important;
                    text-transform: uppercase !important;
                    letter-spacing: 0.8px !important;
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4), 0 2px 4px rgba(0,0,0,0.1) !important;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                    display: inline-flex !important;
                    align-items: center !important;
                    gap: 10px !important;
                    text-decoration: none !important;
                    border: none !important;
                    position: relative !important;
                    overflow: hidden !important;
                }
                .import-async-button-modern::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: -100%;
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                    transition: left 0.5s;
                }
                .import-async-button-modern:hover::before {
                    left: 100%;
                }
                .import-async-button-modern:hover {
                    transform: translateY(-3px) scale(1.02) !important;
                    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5), 0 4px 8px rgba(0,0,0,0.15) !important;
                    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
                }
                .import-async-button-modern:active {
                    transform: translateY(-1px) scale(0.98) !important;
                    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3) !important;
                }
                .import-async-button-modern .btn-icon {
                    font-size: 15px !important;
                    filter: drop-shadow(0 1px 2px rgba(0,0,0,0.2)) !important;
                    transition: transform 0.3s ease !important;
                }
                .import-async-button-modern:hover .btn-icon {
                    transform: translateY(-2px) rotate(5deg) !important;
                }
                .import-async-button-modern .btn-text {
                    white-space: nowrap !important;
                    position: relative !important;
                    z-index: 1 !important;
                }
            `;
            if (!document.querySelector('style[data-import-button]')) {
                style.setAttribute('data-import-button', 'true');
                document.head.appendChild(style);
            }
            
            li.appendChild(importBtn);
            objectTools.appendChild(li);
            
            console.log('✅ Bouton import asynchrone ajouté dans object-tools');
            return;
        }
        
        // Si object-tools n'existe pas, essayer d'ajouter dans le header
        const contentHeader = document.querySelector('.content-header, .card-header, .box-header');
        if (contentHeader) {
            const importUrl = '/admin/masterdata/product/import-async/';
            const existingBtn = contentHeader.querySelector('a[href="' + importUrl + '"]');
            if (existingBtn) {
                return;
            }
            
            const importBtn = document.createElement('a');
            importBtn.href = importUrl;
            importBtn.className = 'import-async-button-modern';
            importBtn.style.cssText = 'float: right; margin-top: 10px;';
            importBtn.innerHTML = '<i class="fas fa-cloud-upload-alt btn-icon"></i><span class="btn-text">Import asynchrone</span>';
            contentHeader.appendChild(importBtn);
            console.log('✅ Bouton ajouté dans le header');
        }
    }
    
    // Essayer plusieurs fois (au cas où le DOM n'est pas encore prêt)
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', addImportButton);
    } else {
        addImportButton();
    }
    
    // Essayer aussi après un délai (pour Jazzmin qui charge après)
    setTimeout(addImportButton, 500);
    setTimeout(addImportButton, 1500);
    setTimeout(addImportButton, 3000);
})();

