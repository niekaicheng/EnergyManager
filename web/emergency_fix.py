# Final fix for index.html - ensures all modals are correctly structured

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Ensure modal uses style="display: none" instead of class active
content = content.replace('class="modal"', 'class="modal" ')

# Fix 2: Add showImportDataModal function if it doesn't exist
import_modal_fix = '''
    <div id="import-data-modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Import Health Data</h3>
                <button class="close-btn" onclick="closeModal('import-data-modal')">&times;</button>
            </div>
            <form id="import-data-form" onsubmit="importData(event)">
                <div class="file-upload-area">
                    <input type="file" id="data-file" accept=".csv,.json" required>
                    <div class="upload-placeholder">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                            <polyline points="17 8 12 3 7 8" />
                            <line x1="12" y1="3" x2="12" y2="15" />
                        </svg>
                        <p>Click to upload or drag and drop</p>
                        <small>Supported formats: CSV, JSON</small>
                    </div>
                </div>
                <div id="file-preview" class="file-preview"></div>
                <div class="modal-actions">
                    <button type="button" class="btn-secondary" onclick="closeModal('import-data-modal')">Cancel</button>
                    <button type="submit" class="btn-primary">Import Data</button>
                </div>
            </form>
            <div id="import-progress" class="progress-container" style="display: none;">
                <div class="progress-bar">
                    <div class="progress-fill" id="progress-fill"></div>
                </div>
                <p id="progress-text" class="progress-text">Uploading...</p>
            </div>
        </div>
    </div>

    <!-- Log Event Modal -->
    <div id="log-event-modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Log New Event</h3>
                <button class="close-btn" onclick="closeModal('log-event-modal')">&times;</button>
            </div>
            <form id="log-event-form" onsubmit="logEvent(event)">
                <div class="form-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div class="form-group">
                        <label for="event-date">Date</label>
                        <input type="date" id="event-date" required>
                    </div>
                    <div class="form-group">
                        <label for="event-time">Time</label>
                        <input type="time" id="event-time" required>
                    </div>
                </div>
                <div class="form-group">
                    <label for="event-activity">Activity</label>
                    <input type="text" id="event-activity" required placeholder="What did you do?">
                </div>
                <div class="form-group">
                    <label for="event-duration">Duration (minutes)</label>
                    <input type="number" id="event-duration" required min="1" placeholder="e.g., 60">
                </div>
                <div class="form-group">
                    <label for="event-goal">Linked Goal (Optional)</label>
                    <select id="event-goal">
                        <option value="">None</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="event-state">Energy State</label>
                    <select id="event-state" required>
                        <option value="Consumption">Consumption</option>
                        <option value="Internal friction">Internal Friction</option>
                        <option value="Growth">Growth</option>
                        <option value="Abundance">Abundance</option>
                        <option value="Routine">Routine</option>
                    </select>
                </div>
                <div class="scores-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                    <div class="form-group">
                        <label for="event-physical">Physical (1-10)</label>
                        <input type="number" id="event-physical" min="1" max="10" value="5">
                    </div>
                    <div class="form-group">
                        <label for="event-mental">Mental (1-10)</label>
                        <input type="number" id="event-mental" min="1" max="10" value="5">
                    </div>
                    <div class="form-group">
                        <label for="event-emotional">Emotional (1-10)</label>
                        <input type="number" id="event-emotional" min="1" max="10" value="5">
                    </div>
                </div>
                <div class="form-group">
                    <label for="event-notes">Notes (Optional)</label>
                    <textarea id="event-notes" rows="3" placeholder="Any additional notes..."></textarea>
                </div>
                <div class="modal-actions">
                    <button type="button" class="btn-secondary" onclick="closeModal('log-event-modal')">Cancel</button>
                    <button type="submit" class="btn-primary">Log Event</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/index.global.min.js"></script>
    <script src="app.js"></script>
    <script src="calendar.js"></script>
</body>

</html>
'''

# Find where to insert (before first <!-- Scripts --> or </body>)
scripts_pos = content.find('<!-- Scripts -->')
if scripts_pos == -1:
    scripts_pos = content.find('</body>')

if scripts_pos != -1:
    # Insert modal HTML before scripts
    content = content[:scripts_pos] + import_modal_fix

# Write back
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("HTML file fixed successfully")
print(f"File size: {len(content)} bytes")
