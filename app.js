const API_BASE = "http://localhost:8080";
let currentFilePayload = null;

function resetDashboardState() {
    document.getElementById('statusPlaceholder').classList.remove('hidden');
    document.getElementById('matchDisplayArea').classList.add('hidden');
    document.getElementById('newCoralActionPanel').classList.add('hidden');
    document.getElementById('cardsList').innerHTML = '';
}

document.getElementById('imageInput').onchange = function (e) {
    const file = e.target.files[0];
    const site = document.getElementById('siteName').value.trim();

    if (!file) return;
    if (!site) {
        alert("Please populate or select a Dive Site before selecting files.");
        document.getElementById('imageInput').value = "";
        return;
    }

    currentFilePayload = file;

    // Trigger preview container and visibility classes
    document.getElementById('imagePreview').src = URL.createObjectURL(file);
    document.getElementById('previewContainer').classList.remove('hidden');
    document.getElementById('statusPlaceholder').classList.add('hidden');
    document.getElementById('loader').classList.remove('hidden');
    document.getElementById('matchDisplayArea').classList.add('hidden');
    document.getElementById('newCoralActionPanel').classList.add('hidden');

    let formData = new FormData();
    formData.append('image', file);
    formData.append('site_name', site);

    fetch(`${API_BASE}/match-coral`, { method: 'POST', body: formData })
        .then(res => {
            if (!res.ok) throw new Error("API route lookup error context.");
            return res.json();
        })
        .then(data => {
            document.getElementById('loader').classList.add('hidden');
            document.getElementById('matchDisplayArea').classList.remove('hidden');
            document.getElementById('newCoralActionPanel').classList.remove('hidden');
            
            const listContainer = document.getElementById('cardsList');
            listContainer.innerHTML = '';

            if (!data.matches || data.matches.length === 0) {
                listContainer.innerHTML = `
                    <div class="p-6 bg-slate-950 text-slate-500 rounded-xl border border-slate-800 font-mono text-xs text-center">
                        Zero vector alignments matched within site parameters. Click the button below to register a new baseline configuration profile.
                    </div>`;
                return;
            }

            // Build large vertical stack component cards (1 per row)
            data.matches.forEach(match => {
                const pct = (match.similarity * 100).toFixed(1);
                const card = document.createElement('div');
                card.className = "bg-slate-950 rounded-xl p-4 border border-slate-850 flex flex-col shadow-lg space-y-4 w-full";
                
                card.innerHTML = `
                    <div class="space-y-3 w-full">
                        <div class="flex justify-between items-center border-b border-slate-900 pb-2">
                            <span class="text-sm font-bold text-emerald-400 font-mono tracking-wide">${match.coral_id}</span>
                            <span class="text-xs font-mono font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">${pct}% Match Confidence</span>
                        </div>
                        <!-- High Resolution 4:3 Aspect Safe Center Cropping Container Box -->
                        <div class="w-full aspect-[4/3] rounded-lg overflow-hidden bg-slate-900 border border-slate-950 shadow-inner">
                            <img src="${match.storage_url}" class="w-full h-full object-cover object-center hover:scale-[1.01] transition-transform duration-200" onerror="this.src='https://placehold.co'">
                        </div>
                    </div>
                    <button class="w-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-extrabold py-3 rounded-xl shadow-md transition-all tracking-wider uppercase font-mono cursor-pointer flex items-center justify-center active:scale-[0.99]">
                        🤝 Link Verification Session to This Profile
                    </button>
                `;

                card.querySelector('button').onclick = () => {
                    executeMonitoringCommit(match.coral_id, site, match.storage_url);
                };

                listContainer.appendChild(card);
            });
        })
        .catch(() => {
            document.getElementById('loader').classList.add('hidden');
            resetDashboardState();
            alert("Error running similarity arrays check against cloud engine endpoints.");
        });
};

function executeMonitoringCommit(coralId, site, storageUrl) {
    let commitForm = new FormData();
    commitForm.append('coral_id', coralId);
    commitForm.append('site_name', site);
    commitForm.append('storage_url', storageUrl);

    fetch(`${API_BASE}/commit-session`, { method: 'POST', body: commitForm })
        .then(res => res.json())
        .then(() => {
            alert(`Success! Entry tracked against individual profile registry index: ${coralId}`);
            location.reload();
        });
}

document.getElementById('registerNewBtn').onclick = function() {
    const site = document.getElementById('siteName').value.trim();
    if (!currentFilePayload || !site) return;

    const uniqueTimestamp = Date.now().toString().slice(-4);
    const shortSiteCode = site.substring(0, 3).toUpperCase();
    const generatedCoralId = `CRL-${shortSiteCode}-${uniqueTimestamp}`;

    let regForm = new FormData();
    regForm.append('image', currentFilePayload);
    regForm.append('site_name', site);
    regForm.append('coral_id', generatedCoralId);

    this.innerText = "Processing matrix arrays...";
    this.disabled = true;

    fetch(`${API_BASE}/register-new`, { method: 'POST', body: regForm })
        .then(res => res.json())
        .then(result => {
            this.disabled = false;
            this.innerText = "➕ Log As New Colony Discovery";
            if (result.error) throw new Error(result.error);
            alert(`Success! Profile individual cataloged under structural tag reference identifier: ${generatedCoralId}`);
            location.reload();
        })
        .catch(err => {
            this.disabled = false;
            this.innerText = "➕ Log As New Colony Discovery";
            alert(`Registration Error context details: ${err.message}`);
        });
};
