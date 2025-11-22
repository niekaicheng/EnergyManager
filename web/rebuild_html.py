# Rebuild clean index.html with all modals properly structured

import re

# Read the broken file
with open('index_clean.backup', 'r', encoding='utf-8') as f:
    content = f.read()

# Find where modals section ends (should be before scripts)
# Remove any malformed modal content first
lines = content.split('\n')

# Find the line with "<!-- Scripts -->"
scripts_start = -1
for i, line in enumerate(lines):
    if '<!-- Scripts -->' in line:
        scripts_start = i
        break

if scripts_start == -1:
    print("ERROR: Could not find scripts section")
    exit(1)

# Everything before scripts
before_scripts = '\n'.join(lines[:scripts_start])

# Check if we have proper modal closures
# Count opening and closing div tags in the modals section
# This is a simple heuristic
if before_scripts.count('<div') != before_scripts.count('</div>'):
    print(f"WARNING: Unmatched div tags. Opening: {before_scripts.count('<div')}, Closing: {before_scripts.count('</div>')}")

# Add missing closing tags for Edit Goal Modal
if '</form>' in before_scripts and before_scripts.count('</form>') < before_scripts.count('<form'):
    print("Adding missing form closing tags")
    # Find the Edit Goal Modal and fix it
    before_scripts = re.sub(
        r'(\s*<input type="number" id="edit-goal-cost"[^>]*>.*?<small>Negative for consumption, positive for recovery</small>\s*</div>)\s*<div class="modal-actions">\s*</div>',
        r'\1\n                <div class="modal-actions">\n                    <button type="button" class="btn-secondary" onclick="closeModal(\'edit-goal-modal\')">Cancel</button>\n                    <button type="submit" class="btn-primary">Update Goal</button>\n                </div>\n            </form>\n        </div>\n    </div>',
        before_scripts,
        flags=re.DOTALL
    )

# Add the Log Event Modal right before scripts
log_event_modal = '''
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
'''

# Scripts section
scripts = '''
    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/index.global.min.js"></script>
    <script src="app.js"></script>
    <script src="calendar.js"></script>
</body>

</html>
'''

# Combine everything
final_content = before_scripts + log_event_modal + scripts

# Write to index.html
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(final_content)

print("✓ HTML file rebuilt successfully!")
print(f"  Total length: {len(final_content)} characters")
print(f"  Total lines: {final_content.count(chr(10))}")
