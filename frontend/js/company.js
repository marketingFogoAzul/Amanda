// frontend/js/company.js

/**
 * Lógica do Painel da Empresa (company-panel.html).
 */

document.addEventListener('DOMContentLoaded', () => {
    // Verifica se está na página correta (e se o app.js já rodou)
    if (!$('#company-panel-page')) { // (Adicione id="company-panel-page" ao body do company-panel.html)
        // return; // Se não for a página, não faz nada
    }

    // Referências do DOM
    const teamTableBody = $('#team-table-body');
    const addSellerForm = $('#add-seller-form');
    const addSellerButton = $('#add-seller-button');

    // 1. Carregar a equipe da empresa
    loadTeam();

    // 2. Event Listener para adicionar vendedor
    addSellerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const fullName = $('#seller-name').value;
        const email = $('#seller-email').value;
        const password = $('#seller-password').value;

        addSellerButton.disabled = true;
        addSellerButton.textContent = 'Adicionando...';
        hideMessage('seller-error-message');
        hideMessage('seller-success-message');

        try {
            // Chama a API (definida em api.js)
            const data = await fetchApi('/company/add_seller', 'POST', {
                full_name: fullName,
                email: email,
                password: password
            }, true); // true = requer autenticação

            // Sucesso
            showMessage('seller-success-message', 'Vendedor adicionado com sucesso!', 'success');
            addSellerForm.reset(); // Limpa o formulário
            
            // Adiciona o novo vendedor à tabela (sem recarregar a página)
            renderTeamMember(data.user);

        } catch (error) {
            showMessage('seller-error-message', error.message);
        } finally {
            addSellerButton.disabled = false;
            addSellerButton.textContent = 'Adicionar';
        }
    });

    /**
     * Busca a equipe na API e renderiza na tabela.
     */
    async function loadTeam() {
        try {
            const team = await fetchApi('/company/team', 'GET', null, true);
            
            teamTableBody.innerHTML = ''; // Limpa a tabela
            if (team.length === 0) {
                teamTableBody.innerHTML = '<tr><td colspan="5">Nenhum membro na equipe.</td></tr>';
                return;
            }
            
            team.forEach(renderTeamMember);

        } catch (error) {
            showMessage('seller-error-message', `Erro ao carregar equipe: ${error.message}`);
        }
    }

    /**
     * Renderiza um único membro na tabela.
     */
    function renderTeamMember(user) {
        const statusClass = user.is_active ? 'active' : 'blocked';
        const statusText = user.is_active ? 'Ativo' : (user.is_blocked ? 'Bloqueado' : 'Inativo');

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${user.full_name}</td>
            <td>${user.email}</td>
            <td>${user.role}</td>
            <td><span class="status ${statusClass}">${statusText}</span></td>
            <td>
                <button class="btn-icon" title="Editar"><i data-feather="edit-2"></i></button>
                <button class="btn-icon btn-danger" title="Desativar"><i data-feather="trash-2"></i></button>
            </td>
        `;
        
        teamTableBody.appendChild(tr);
        feather.replace(); // Ativa os ícones
    }
});