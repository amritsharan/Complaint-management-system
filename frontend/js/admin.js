const API_URL = 'http://127.0.0.1:8002';

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');

    if (!token || role !== 'admin') {
        window.location.href = '/';
        return;
    }

    const complaintsList = document.getElementById('admin-complaints-list');
    const filterStatus = document.getElementById('filter-status');
    const refreshBtn = document.getElementById('refresh-btn');
    const logoutBtn = document.getElementById('logout-btn');

    const updateModal = document.getElementById('update-modal');
    const closeModal = document.getElementById('close-modal');
    const updateForm = document.getElementById('update-form');

    let allComplaints = [];

    logoutBtn.addEventListener('click', () => {
        localStorage.clear();
        window.location.href = '/';
    });

    const loadAllComplaints = async () => {
        try {
            const response = await fetch(`${API_URL}/admin/complaints`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            allComplaints = await response.json();
            renderComplaints(allComplaints);
        } catch (error) {
            console.error('Failed to load admin complaints:', error);
        }
    };

    const renderComplaints = (complaints) => {
        const statusFilter = filterStatus.value;
        const filtered = statusFilter === 'all'
            ? complaints
            : complaints.filter(c => c.status === statusFilter);

        if (filtered.length === 0) {
            complaintsList.innerHTML = `
                <div class="glass rounded-2xl p-20 text-center text-gray-400 border-dashed border-2">
                    No complaints found matching the criteria.
                </div>
            `;
            return;
        }

        complaintsList.innerHTML = filtered.map(c => `
            <div class="glass rounded-2xl p-8 shadow-sm hover:shadow-md transition-all flex flex-col md:flex-row gap-8 items-start">
                <div class="flex-1">
                    <div class="flex items-center gap-3 mb-4">
                        <span class="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-gray-900 text-white">Priority #${c.priority_rank ?? '-'}</span>
                        <span class="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-100 text-amber-700">Score ${Number(c.priority_score || 0).toFixed(1)}</span>
                        <span class="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${getStatusBadge(c.status)}">${c.status}</span>
                        <span class="text-xs font-semibold text-gray-400">ID: ${c.id}</span>
                    </div>
                    <h3 class="text-xl font-bold text-gray-800 mb-2">${c.title}</h3>
                    <p class="text-gray-600 mb-6 leading-relaxed">${c.description}</p>
                    
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6 border-t border-gray-100">
                        <div>
                            <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-1">Category</p>
                            <p class="text-sm font-semibold text-gray-700">${c.category}</p>
                        </div>
                        <div>
                            <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-1">Date</p>
                            <p class="text-sm font-semibold text-gray-700">${new Date(c.date_created).toLocaleDateString()}</p>
                        </div>
                        <div>
                            <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-1">Evidence</p>
                            ${c.file_url ? `<a href="${c.file_url}" target="_blank" class="text-sm font-semibold text-indigo-600 hover:underline">View File</a>` : '<p class="text-sm font-semibold text-gray-400">None</p>'}
                        </div>
                        <div>
                            <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-1">User ID</p>
                            <p class="text-sm font-semibold text-gray-700">${c.user_id}</p>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 pt-6 mt-6 border-t border-gray-100">
                        <div class="rounded-xl bg-slate-50 p-3">
                            <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-1">TF-IDF</p>
                            <p class="text-sm font-semibold text-gray-700">${Number(c.tfidf_score || 0).toFixed(1)}</p>
                        </div>
                        <div class="rounded-xl bg-slate-50 p-3">
                            <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-1">BM25</p>
                            <p class="text-sm font-semibold text-gray-700">${Number(c.bm25_score || 0).toFixed(1)}</p>
                        </div>
                        <div class="rounded-xl bg-slate-50 p-3">
                            <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-1">Priority</p>
                            <p class="text-sm font-semibold text-gray-700">${Number(c.priority_score || 0).toFixed(1)} / 100</p>
                        </div>
                    </div>
                </div>

                <div class="md:w-64 w-full h-full flex flex-col justify-between border-t md:border-t-0 md:border-l border-gray-100 md:pl-8 pt-6 md:pt-0">
                    <div class="mb-6">
                        <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-2">Remarks</p>
                        <p class="text-xs italic text-gray-500">${c.admin_remarks || 'No remarks added yet.'}</p>
                    </div>
                    <button onclick="openUpdateModal('${c.id}', '${c.status}', '${c.admin_remarks?.replace(/'/g, "\\'") || ''}')" class="w-full py-3 bg-gray-800 text-white rounded-xl font-bold text-sm hover:bg-gray-700 transition-all flex items-center justify-center gap-2">
                        <i data-lucide="edit-3" class="w-4 h-4"></i> Update Status
                    </button>
                </div>
            </div>
        `).join('');
        lucide.createIcons();
    };

    const getStatusBadge = (status) => {
        switch (status) {
            case 'Pending': return 'bg-yellow-100 text-yellow-700';
            case 'In Progress': return 'bg-indigo-100 text-indigo-700';
            case 'Resolved': return 'bg-green-100 text-green-700';
            default: return 'bg-gray-100 text-gray-700';
        }
    };

    // Modal Logic
    window.openUpdateModal = (id, status, remarks) => {
        document.getElementById('modal-complaint-id').value = id;
        document.getElementById('modal-status').value = status;
        document.getElementById('modal-remarks').value = remarks;
        updateModal.classList.remove('hidden');
    };

    closeModal.addEventListener('click', () => updateModal.classList.add('hidden'));

    updateForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('modal-complaint-id').value;
        const status = document.getElementById('modal-status').value;
        const admin_remarks = document.getElementById('modal-remarks').value;

        try {
            const response = await fetch(`${API_URL}/admin/complaints/${id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ status, admin_remarks })
            });

            if (response.ok) {
                updateModal.classList.add('hidden');
                loadAllComplaints();
            } else {
                alert('Update failed');
            }
        } catch (error) {
            console.error('Update error:', error);
        }
    });

    filterStatus.addEventListener('change', () => renderComplaints(allComplaints));
    refreshBtn.addEventListener('click', loadAllComplaints);

    loadAllComplaints();

    const eventSource = new EventSource(`${API_URL}/events?token=${encodeURIComponent(token)}`);
    eventSource.onmessage = () => loadAllComplaints();
    eventSource.onerror = () => {
        console.error('Admin complaint live updates disconnected');
    };

    window.addEventListener('beforeunload', () => eventSource.close());
});
