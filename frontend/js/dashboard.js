const API_URL = 'http://127.0.0.1:8002';

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/';
        return;
    }

    const userDisplay = document.getElementById('user-display');
    const email = localStorage.getItem('email');
    userDisplay.innerText = email;
    userDisplay.classList.remove('hidden');

    const complaintForm = document.getElementById('complaint-form');
    const complaintsList = document.getElementById('complaints-list');
    const logoutBtn = document.getElementById('logout-btn');

    logoutBtn.addEventListener('click', () => {
        localStorage.clear();
        window.location.href = '/';
    });

    // Load Complaints
    const loadComplaints = async () => {
        try {
            const response = await fetch(`${API_URL}/complaints`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const complaints = await response.json();

            if (complaints.length === 0) {
                complaintsList.innerHTML = `
                    <div class="glass rounded-2xl p-12 text-center text-gray-500 border-dashed border-2">
                        No complaints submitted yet. Use the form to start.
                    </div>
                `;
                return;
            }

            complaintsList.innerHTML = complaints.map(c => `
                <div class="glass rounded-2xl p-6 shadow-sm border-l-4 ${getStatusColor(c.status)}">
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <span class="text-xs font-bold uppercase tracking-wider px-2 py-1 rounded bg-gray-100 text-gray-600 mb-2 inline-block">${c.category}</span>
                            <h3 class="text-lg font-bold text-gray-800">${c.title}</h3>
                        </div>
                        <span class="px-3 py-1 rounded-full text-xs font-bold ${getStatusBadge(c.status)}">${c.status}</span>
                    </div>
                    <p class="text-gray-600 text-sm mb-4">${c.description}</p>
                    ${c.file_url ? `<a href="${c.file_url}" target="_blank" class="text-indigo-600 text-xs font-medium flex items-center gap-1 mb-4 hover:underline"><i data-lucide="link" class="w-3 h-3"></i> View Evidence</a>` : ''}
                    <div class="pt-4 border-t border-gray-100 flex flex-col gap-2">
                        <div class="flex justify-between items-center text-[10px] text-gray-400 uppercase font-bold tracking-widest">
                            <span>Submitted on ${new Date(c.date_created).toLocaleDateString()}</span>
                            <span>ID: ${c.id}</span>
                        </div>
                        ${c.admin_remarks ? `
                            <div class="bg-indigo-50 p-3 rounded-xl mt-2">
                                <p class="text-xs font-bold text-indigo-800 mb-1 flex items-center gap-1"><i data-lucide="message-square" class="w-3 h-3"></i> Admin Remarks:</p>
                                <p class="text-xs text-indigo-600 italic">${c.admin_remarks}</p>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `).join('');
            lucide.createIcons();
        } catch (error) {
            console.error('Failed to load complaints:', error);
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'Pending': return 'border-yellow-400';
            case 'In Progress': return 'border-indigo-500';
            case 'Resolved': return 'border-green-500';
            default: return 'border-gray-300';
        }
    };

    const getStatusBadge = (status) => {
        switch (status) {
            case 'Pending': return 'bg-yellow-100 text-yellow-700';
            case 'In Progress': return 'bg-indigo-100 text-indigo-700';
            case 'Resolved': return 'bg-green-100 text-green-700';
            default: return 'bg-gray-100 text-gray-700';
        }
    };

    // Submit Complaint
    complaintForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const complaintData = {
            title: document.getElementById('title').value,
            category: document.getElementById('category').value,
            description: document.getElementById('description').value,
            file_url: document.getElementById('file_url').value || null
        };

        try {
            const response = await fetch(`${API_URL}/complaints`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(complaintData)
            });

            if (response.ok) {
                alert('Complaint submitted successfully!');
                complaintForm.reset();
                loadComplaints();
            } else {
                alert('Failed to submit complaint');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Server error');
        }
    });

    loadComplaints();

    const eventSource = new EventSource(`${API_URL}/events?token=${encodeURIComponent(token)}`);
    eventSource.onmessage = () => loadComplaints();
    eventSource.onerror = () => {
        console.error('Complaint live updates disconnected');
    };

    window.addEventListener('beforeunload', () => eventSource.close());
});
