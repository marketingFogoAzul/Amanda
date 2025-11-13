// frontend/js/admin.js

/**
 * Lógica do Painel Administrativo (admin-panel.html).
 */

document.addEventListener('DOMContentLoaded', () => {
    // Verifica se está na página correta
    if (!$('#admin-panel-page')) { // (Adicione id="admin-panel-page" ao body do admin-panel.html)
       // return;
    }
    
    // Referências do DOM
    const usersTableBody = $('#admin-users-table-body');
    const companiesTableBody = $('#admin-companies-table-body');
    const reportsTableBody = $('#admin-reports-table-body');
    const tabs = $$('.tab-link');

    // Mapeamento dos Cargos (para o <select>)
    const ROLES_MAP = {
        0: "Admin ZIPBUM",
        1: "Helper Nível 1",
        2: "Helper Nível 2",
        3: "Helper Nível 3",
        4: "Representante",
        5: "Vendedor",
        6: "Bloqueado",
        7: "Developer"
    };

    // 1. Carrega o conteúdo da primeira aba (Usuários)
    loadAllUsers();

    // 2. Adiciona listeners para trocar de aba
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.dataset.tab;
            if (tabId === 'tab-users') loadAllUsers();
            if (tabId === 'tab-companies') loadAllCompanies();
            if (tabId === 'tab-reports') loadAllReports();
        });
    });

    /**
     * Carrega a lista de TODOS os usuários.
     */
    async function loadAllUsers() {
        try {
            usersTableBody.innerHTML = '<tr><td colspan="5">Carregando...</td></tr>';
            const users = await fetchApi('/admin/users', 'GET', null, true);
            
            usersTableBody.innerHTML = '';
            if (users.length === 0) {
                usersTableBody.innerHTML = '<tr><td colspan="5">Nenhum usuário encontrado.</td></tr>';
                return;
            }
            users.forEach(renderUserRow);
        } catch (error) {
            usersTableBody.innerHTML = `<tr><td colspan="5">Erro: ${error.message}</td></tr>`;
        }
    }
    
    /**
     * Renderiza um usuário na tabela de Admin.
     */
    function renderUserRow(user) {
        // Cria o <select> para mudança de cargo
        let roleOptions = Object.keys(ROLES_MAP).map(level => 
            `<option value="${level}" ${user.role_level == level ? 'selected' : ''}>
                ${ROLES_MAP[level]}
            </option>`
        ).join('');
        
        let selectHtml = `<select class="role-select" data-user-id="${user.id}">${roleOptions}</select>`;

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${user.full_name}</td>
            <td>${user.email}</td>
            <td>${user.company_id || 'N/A'}</td> <td>${selectHtml}</td>
            <td>
                <button class="btn-icon" title="Salvar Cargo" data-action="save" data-user-id="${user.id}">
                    <i data-feather="save"></i>
                </button>
            </td>
        `;
        usersTableBody.appendChild(tr);
        feather.replace(); // Ativa os ícones
    }

    /**
     * Carrega a lista de TODAS as empresas.
     */
    async function loadAllCompanies() {
        try {
            companiesTableBody.innerHTML = '<tr><td colspan="5">Carregando...</td></tr>';
            const companies = await fetchApi('/admin/companies', 'GET', null, true);

            companiesTableBody.innerHTML = '';
            companies.forEach(company => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${company.razao_social}</td>
                    <td>${company.nome_fantasia || 'N/A'}</td>
                    <td>${company.cnpj}</td>
                    <td>${company.uf}</td>
                    <td><button class="btn-icon btn-danger" title="Desativar Empresa"><i data-feather="trash-2"></i></button></td>
                `;
                companiesTableBody.appendChild(tr);
            });
            feather.replace();
        } catch (error) {
            companiesTableBody.innerHTML = `<tr><td colspan="5">Erro: ${error.message}</td></tr>`;
        }
    }
    
    /**
     * Carrega a lista de denúncias pendentes.
     */
    async function loadAllReports() {
        try {
            reportsTableBody.innerHTML = '<tr><td colspan="5">Carregando...</td></tr>';
            const reports = await fetchApi('/admin/reports', 'GET', null, true);

            reportsTableBody.innerHTML = '';
            reports.forEach(report => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${new Date(report.created_at).toLocaleString('pt-BR')}</td>
                    <td>${report.category}</td>
                    <td>${report.reported_user_id.substring(0, 8)}...</td>
                    <td>${report.reporter_id.substring(0, 8)}...</td>
                    <td>
                        <button class="btn-icon" title="Ver Detalhes"><i data-feather="eye"></i></button>
                        <button class="btn-icon" title="Resolver"><i data-feather="check-square"></i></button>
                    </td>
                `;
                reportsTableBody.appendChild(tr);
            });
            feather.replace();
        } catch (error) {
            reportsTableBody.innerHTML = `<tr><td colspan="5">Erro: ${error.message}</td></tr>`;
        }
    }

    // --- Ação de Mudar Cargo (Event Delegation) ---
    usersTableBody.addEventListener('click', async (e) => {
        const saveButton = e.target.closest('button[data-action="save"]');
        if (!saveButton) return;
        
        const userId = saveButton.dataset.userId;
        const select = $(`select[data-user-id="${userId}"]`);
        const newRoleLevel = select.value;

        // Feedback visual
        saveButton.innerHTML = '<i data-feather="loader" class="spin"></i>';
        feather.replace();

        try {
            // Chama a API de mudança de cargo
            await fetchApi('/admin/user/changerole', 'POST', {
                user_id: userId,
                new_role_level: newRoleLevel
            }, true);
            
            saveButton.innerHTML = '<i data-feather="check"></i>'; // Sucesso
            setTimeout(() => saveButton.innerHTML = '<i data-feather="save"></i>', 2000);

        } catch (error) {
            alert(`Erro ao salvar: ${error.message}`);
            saveButton.innerHTML = '<i data-feather="save"></i>';
        }
        feather.replace();
    });
});