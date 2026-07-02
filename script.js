// script.js

// Define the base URL for the FastAPI backend
const API_BASE_URL = 'https://fifa-world-cup-predictor-17ns.onrender.com';

/**
 * Fetches upcoming fixtures from the backend and dynamically generates
 * HTML for the match cards.
 */
async function loadFixtures() {
    const container = document.getElementById('fixtures_container');
    if (!container) return; // Ensure the element exists in the DOM

    // Display a loading state
    container.innerHTML = '<p>Loading fixtures and predictions...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/fixtures`);
        if (!response.ok) throw new Error('Network response was not ok');

        const fixtures = await response.json();

        // Clear the loading state
        container.innerHTML = '';

        // Iterate through the JSON response to build the UI
        fixtures.forEach(fixture => {
            const card = document.createElement('div');
            card.className = 'fixture-card';
            // Assuming your CSS has styles for .fixture-card, .matchup, .team, etc.

            // Format HTML for the card, dynamically mapping progress bar widths
            card.innerHTML = `
                <div class="matchup">
                    <h3 class="team team-a">${fixture.team_a}</h3>
                    <span class="vs">vs</span>
                    <h3 class="team team-b">${fixture.team_b}</h3>
                </div>
                <div class="predictions">
                    <div class="prob-row">
                        <label>${fixture.team_a} Win Probability</label>
                        <div class="progress-bar-container" style="background-color: #ddd; height: 20px; border-radius: 10px; overflow: hidden; margin-bottom: 10px;">
                            <div class="progress-bar" style="background-color: #4CAF50; height: 100%; width: ${fixture.team_a_prob}%;"></div>
                        </div>
                        <span class="percent">${fixture.team_a_prob}%</span>
                    </div>
                    <div class="prob-row" style="margin-top: 15px;">
                        <label>${fixture.team_b} Win Probability</label>
                        <div class="progress-bar-container" style="background-color: #ddd; height: 20px; border-radius: 10px; overflow: hidden; margin-bottom: 10px;">
                            <div class="progress-bar" style="background-color: #2196F3; height: 100%; width: ${fixture.team_b_prob}%;"></div>
                        </div>
                        <span class="percent">${fixture.team_b_prob}%</span>
                    </div>
                </div>
                <hr>
            `;

            container.appendChild(card);
        });

    } catch (error) {
        console.error('Error fetching fixtures:', error);
        container.innerHTML = '<p style="color: red;">Error loading fixtures. Please ensure the FastAPI backend is running.</p>';
    }
}

/**
 * Fetches the top 20 players from the backend and dynamically populates
 * the players table.
 */
async function loadPlayers() {
    const tbody = document.getElementById('players_table_body');
    if (!tbody) return; // Ensure the element exists in the DOM

    tbody.innerHTML = '<tr><td colspan="5">Loading player statistics...</td></tr>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/players`);
        if (!response.ok) throw new Error('Network response was not ok');

        const players = await response.json();

        // Clear the loading state
        tbody.innerHTML = '';

        // Iterate through the array to create table rows
        players.forEach(player => {
            const tr = document.createElement('tr');

            // Format numbers safely to 4 decimal places
            const decay = typeof player.decay_weight === 'number' ? player.decay_weight.toFixed(4) : player.decay_weight;
            const form = typeof player.current_form_score === 'number' ? player.current_form_score.toFixed(4) : player.current_form_score;

            tr.innerHTML = `
                <td>${player.Name || 'Unknown'}</td>
                <td>${player.Country || 'Unknown'}</td>
                <td>${player.Position || 'Unknown'}</td>
                <td>${decay}</td>
                <td><strong>${form}</strong></td>
            `;

            tbody.appendChild(tr);
        });

    } catch (error) {
        console.error('Error fetching players:', error);
        tbody.innerHTML = '<tr><td colspan="5" style="color: red;">Error loading player data. Please ensure the backend is running.</td></tr>';
    }
}

/**
 * Sets up event listeners to handle the tab switching between 
 * "Upcoming Fixtures" and "Player Stats".
 */
function setupTabs() {
    const fixturesTab = document.getElementById('tab_fixtures');
    const playersTab = document.getElementById('tab_players');
    const fixturesSection = document.getElementById('section_fixtures');
    const playersSection = document.getElementById('section_players');

    if (!fixturesTab || !playersTab || !fixturesSection || !playersSection) {
        console.warn('Tab elements not found in the DOM.');
        return;
    }

    fixturesTab.addEventListener('click', (e) => {
        e.preventDefault();
        // Update tab styles
        fixturesTab.classList.add('active');
        playersTab.classList.remove('active');
        // Toggle visibility
        fixturesSection.style.display = 'block';
        playersSection.style.display = 'none';
    });

    playersTab.addEventListener('click', (e) => {
        e.preventDefault();
        // Update tab styles
        playersTab.classList.add('active');
        fixturesTab.classList.remove('active');
        // Toggle visibility
        playersSection.style.display = 'block';
        fixturesSection.style.display = 'none';
    });
}

// Initialize the logic when the HTML document is fully parsed
document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    loadFixtures();
    loadPlayers();
});
