// script.js

// Configure the base URL for the live Render backend
const API_BASE_URL = 'https://fifa-world-cup-predictor-17ns.onrender.com';

/**
 * Fetches upcoming fixtures from the backend and dynamically generates HTML for the match cards.
 */
async function loadFixtures() {
    const container = document.getElementById('fixtures_container');
    if (!container) return;
    
    // Clear out hardcoded sample cards
    container.innerHTML = '<p class="text-on-surface-variant">Loading fixtures and predictions...</p>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/fixtures`);
        if (!response.ok) throw new Error('Network response was not ok');
        
        const fixtures = await response.json();
        
        // Clear the loading state
        container.innerHTML = ''; 
        
        fixtures.forEach(fixture => {
            const card = document.createElement('div');
            card.className = 'glass-panel rounded-xl p-6 glow-hover transition-all duration-300';
            
            // Replicate the Tailwind card structure from the HTML template
            card.innerHTML = `
                <div class="text-xs text-on-surface-variant uppercase tracking-wider mb-4 flex justify-between">
                    <span>Quarter-Final</span>
                    <span>14:00 GMT</span>
                </div>
                <div class="flex justify-between items-center mb-6">
                    <div class="flex flex-col items-center gap-2">
                        <div class="w-12 h-12 rounded-full overflow-hidden bg-surface-container flex items-center justify-center border border-primary/20">
                            <!-- Placeholder text since dynamic flags are not available -->
                            <span class="font-bold text-on-surface">${fixture.team_a.substring(0,3).toUpperCase()}</span>
                        </div>
                        <span class="font-bold">${fixture.team_a.substring(0,3).toUpperCase()}</span>
                    </div>
                    <div class="text-xl font-headline text-on-surface-variant">VS</div>
                    <div class="flex flex-col items-center gap-2">
                        <div class="w-12 h-12 rounded-full overflow-hidden bg-surface-container flex items-center justify-center border border-primary/20">
                            <!-- Placeholder text since dynamic flags are not available -->
                            <span class="font-bold text-on-surface">${fixture.team_b.substring(0,3).toUpperCase()}</span>
                        </div>
                        <span class="font-bold">${fixture.team_b.substring(0,3).toUpperCase()}</span>
                    </div>
                </div>
                <div class="space-y-2">
                    <div class="flex justify-between text-sm text-on-surface-variant">
                        <span>Win Probability</span>
                        <span class="text-primary font-bold">${fixture.team_a_prob}% - ${fixture.team_b_prob}%</span>
                    </div>
                    <div class="h-2 w-full bg-surface-container rounded-full overflow-hidden flex">
                        <div class="h-full bg-primary" style="width: ${fixture.team_a_prob}%"></div>
                        <div class="h-full bg-tertiary" style="width: ${fixture.team_b_prob}%"></div>
                    </div>
                </div>
            `;
            
            container.appendChild(card);
        });
        
    } catch (error) {
        console.error('Error fetching fixtures:', error);
        container.innerHTML = '<p class="text-error">Error loading fixtures. Please ensure the FastAPI backend is running.</p>';
    }
}

/**
 * Fetches the top players from the backend and dynamically populates the players table.
 */
async function loadPlayers() {
    const tbody = document.getElementById('players_table_body');
    if (!tbody) return;
    
    // Clear out the hardcoded sample rows
    tbody.innerHTML = '<tr><td colspan="4" class="py-4 px-6 text-on-surface-variant">Loading player statistics...</td></tr>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/players`);
        if (!response.ok) throw new Error('Network response was not ok');
        
        const players = await response.json();
        
        // Store loaded players globally for the search filter
        window.allPlayers = players;
        renderPlayersTable(players);
        
    } catch (error) {
        console.error('Error fetching players:', error);
        tbody.innerHTML = '<tr><td colspan="4" class="py-4 px-6 text-error">Error loading player data.</td></tr>';
    }
}

/**
 * Renders the provided array of players into the table body.
 */
function renderPlayersTable(playersArray) {
    const tbody = document.getElementById('players_table_body');
    if (!tbody) return;
    
    tbody.innerHTML = ''; // Clear existing contents
    
    if (playersArray.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="py-4 px-6 text-on-surface-variant">No players found matching the search.</td></tr>';
        return;
    }

    playersArray.forEach(player => {
        const tr = document.createElement('tr');
        tr.className = "border-b border-primary/5 hover:bg-primary/5 transition-colors";
        
        const formValue = typeof player.current_form_score === 'number' ? player.current_form_score : parseFloat(player.current_form_score || 0);
        
        // Multiply by 100 since the simulated xG base might be small (0.0 to 1.5)
        const displayForm = formValue * 100;
        
        let badgeHTML = '';
        if (displayForm > 85) {
            badgeHTML = `<span class="px-2 py-1 text-[10px] uppercase tracking-wider rounded bg-green-500/20 text-green-400 border border-green-500/30">Hot</span>`;
        } else {
            badgeHTML = `<span class="px-2 py-1 text-[10px] uppercase tracking-wider rounded bg-red-500/20 text-red-400 border border-red-500/30">Cold</span>`;
        }
        
        tr.innerHTML = `
            <td class="py-4 px-6 font-medium">${player.Name || 'Unknown'}</td>
            <td class="py-4 px-6 text-on-surface-variant">${player.Country || 'Unknown'}</td>
            <td class="py-4 px-6 text-on-surface-variant">${player.Position || 'Unknown'}</td>
            <td class="py-4 px-6 font-bold text-primary flex items-center gap-3">
                ${displayForm.toFixed(1)}
                ${badgeHTML}
            </td>
        `;
        
        tbody.appendChild(tr);
    });
}

/**
 * Adds an event listener to the search input element to filter table rows in real-time.
 */
function setupSearchFilter() {
    // Select the exact input element referenced in the HTML
    const searchInput = document.querySelector('input[placeholder="Search player..."]');
    if (!searchInput) return;

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        
        if (!window.allPlayers) return; // Wait until data is fetched and loaded
        
        const filteredPlayers = window.allPlayers.filter(player => {
            const name = (player.Name || '').toLowerCase();
            const country = (player.Country || '').toLowerCase();
            const position = (player.Position || '').toLowerCase();
            return name.includes(query) || country.includes(query) || position.includes(query);
        });
        
        renderPlayersTable(filteredPlayers);
    });
}

// Trigger data-loading functions sequentially when the DOM is ready.
// This does not break the existing tab-toggling script since that is handled directly within index.html
document.addEventListener('DOMContentLoaded', async () => {
    // Set up real-time search filter
    setupSearchFilter();
    
    // Load data from the backend APIs sequentially
    await loadFixtures();
    await loadPlayers();
});
