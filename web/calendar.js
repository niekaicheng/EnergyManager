// ==================== CALENDAR FUNCTIONALITY ====================

// Global calendar instance
let calendar = null;
let calendarEvents = [];

// Custom prompt function that creates DOM elements instead of using window.prompt
function showCustomPrompt(title, message, defaultValue, callback) {
    // Remove any existing prompts
    const existing = document.getElementById('custom-prompt-overlay');
    if (existing) existing.remove();

    // Create overlay
    const overlay = document.createElement('div');
    overlay.id = 'custom-prompt-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    `;

    // Create dialog
    const dialog = document.createElement('div');
    dialog.style.cssText = `
        background: #1e293b;
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 24px;
        max-width: 400px;
        width: 90%;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8);
    `;

    dialog.innerHTML = `
        <h3 style="margin: 0 0 8px 0; color: #f1f5f9; font-size: 18px;">${title}</h3>
        <p style="margin: 0 0 16px 0; color: #94a3b8; font-size: 14px; white-space: pre-wrap;">${message}</p>
        <input type="text" id="custom-prompt-input" value="${defaultValue}" 
            style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #334155; 
                   background: #0f172a; color: #f1f5f9; font-size: 14px; margin-bottom: 16px;">
        <div style="display: flex; gap: 12px; justify-content: flex-end;">
            <button id="custom-prompt-cancel" 
                style="padding: 10px 20px; border-radius: 6px; border: 1px solid #334155; 
                   background: transparent; color: #94a3b8; cursor: pointer; font-size: 14px;">
                Cancel
            </button>
            <button id="custom-prompt-ok" 
                style="padding: 10px 20px; border-radius: 6px; border: none; 
                       background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                       color: white; cursor: pointer; font-size: 14px; font-weight: 500;">
                OK
            </button>
        </div>
    `;

    overlay.appendChild(dialog);
    document.body.appendChild(overlay);

    const input = document.getElementById('custom-prompt-input');
    const okBtn = document.getElementById('custom-prompt-ok');
    const cancelBtn = document.getElementById('custom-prompt-cancel');

    input.focus();
    input.select();

    const cleanup = () => overlay.remove();

    okBtn.onclick = () => {
        const value = input.value;
        cleanup();
        callback(value);
    };

    cancelBtn.onclick = () => {
        cleanup();
        callback(null);
    };

    input.onkeydown = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            okBtn.click();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            cancelBtn.click();
        }
    };

    overlay.onclick = (e) => {
        if (e.target === overlay) cancelBtn.click();
    };
}

// Initialize calendar when journal page is loaded
async function renderJournal(days = 90) {
    try {
        const events = await fetchEvents(days);
        calendarEvents = events;
        console.log(`Loaded ${events.length} events for ${days} days`);

        if (!calendar) {
            initializeCalendar();
        } else {
            updateCalendarEvents(events);
        }
    } catch (error) {
        console.error('Error loading journal:', error);
    }
}

// Initialize FullCalendar
function initializeCalendar() {
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) {
        console.error('Calendar element not found!');
        return;
    }

    console.log('Initializing calendar with', calendarEvents.length, 'events');

    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridDay',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: ''
        },
        editable: true,
        eventDurationEditable: true,
        height: 'auto',
        slotMinTime: '06:00:00',
        slotMaxTime: '24:00:00',
        allDaySlot: false,

        events: transformEventsToCalendar(calendarEvents),

        eventDidMount: function (info) {
            const event = info.event;
            const props = event.extendedProps;

            let tooltip = null;

            const tooltipHTML = `
                <div style="font-size: 12px; line-height: 1.6; color: #f1f5f9;">
                    <strong style="font-size: 13px;">${event.title}</strong><br>
                    <em>State:</em> ${props.key_state || 'N/A'}<br>
                    <em>Duration:</em> ${props.duration_minutes} mins<br>
                    ${props.goal_name ? `<em>Goal:</em> ${props.goal_name}<br>` : ''}
                    ${props.energy_cost !== undefined ? `<em>Energy:</em> ${props.energy_cost >= 0 ? '+' : ''}${props.energy_cost}<br>` : ''}
                    <small style="color: #94a3b8; margin-top: 4px; display: block;">Drag to move • Double-click to edit</small>
                </div>
            `.trim();

            const removeTooltip = function () {
                if (tooltip && tooltip.parentNode) {
                    tooltip.parentNode.removeChild(tooltip);
                    tooltip = null;
                }
            };

            info.el.addEventListener('mouseenter', function (e) {
                if (tooltip) return;

                tooltip = document.createElement('div');
                tooltip.className = 'event-tooltip';
                tooltip.innerHTML = tooltipHTML;
                tooltip.style.cssText = `
                    position: fixed;
                    background: #1e293b;
                    border: 1px solid rgba(99, 102, 241, 0.3);
                    border-radius: 8px;
                    padding: 12px;
                    z-index: 10000;
                    box-shadow: 0 8px 24px rgba(0,0,0,0.6);
                    max-width: 320px;
                    pointer-events: none;
                `;

                const rect = e.target.getBoundingClientRect();
                tooltip.style.left = (rect.right + 10) + 'px';
                tooltip.style.top = rect.top + 'px';

                document.body.appendChild(tooltip);
            });

            info.el.addEventListener('mouseleave', removeTooltip);
            info.el.addEventListener('mousedown', removeTooltip);

            // Double-click handler
            info.el.addEventListener('dblclick', function () {
                console.log('Double-click detected on:', event.title);
                removeTooltip();

                const currentDate = event.start.toISOString().split('T')[0];
                const currentTime = event.start.toTimeString().slice(0, 5);
                const currentEndTime = event.end ? event.end.toTimeString().slice(0, 5) : '';

                // Step 1: Ask for date
                showCustomPrompt(
                    'Edit Event',
                    `Event: ${event.title}\n\nEnter new date (YYYY-MM-DD):`,
                    currentDate,
                    (newDate) => {
                        if (!newDate) return;

                        // Step 2: Ask for start time
                        showCustomPrompt(
                            'Edit Event',
                            `Date: ${newDate}\n\nEnter new START time (HH:MM):`,
                            currentTime,
                            (newStartTime) => {
                                if (!newStartTime) return;

                                // Step 3: Ask for end time
                                showCustomPrompt(
                                    'Edit Event',
                                    `Start: ${newStartTime}\n\nEnter new END time (HH:MM):`,
                                    currentEndTime,
                                    (newEndTime) => {
                                        if (!newEndTime) return;

                                        try {
                                            const newStartTimestamp = new Date(`${newDate}T${newStartTime}`).toISOString();

                                            // Calculate duration
                                            const start = new Date(`${newDate}T${newStartTime}`);
                                            const end = new Date(`${newDate}T${newEndTime}`);

                                            // Handle overnight events (end time < start time)
                                            if (end < start) {
                                                end.setDate(end.getDate() + 1);
                                            }

                                            const durationMinutes = Math.round((end - start) / 60000);

                                            if (durationMinutes <= 0) {
                                                showNotification('End time must be after start time', 'error');
                                                return;
                                            }

                                            console.log('Updating to:', newStartTimestamp, 'Duration:', durationMinutes);

                                            updateEventTime(event.id, newStartTimestamp, durationMinutes)
                                                .then(() => {
                                                    console.log('Update successful');
                                                    showNotification('Event updated successfully!', 'success');
                                                    loadJournal(90);
                                                })
                                                .catch(err => {
                                                    console.error('Update error:', err);
                                                    showNotification('Error: ' + err.message, 'error');
                                                });
                                        } catch (err) {
                                            console.error('Date parse error:', err);
                                            showNotification('Invalid date/time format', 'error');
                                        }
                                    }
                                );
                            }
                        );
                    }
                );
            });
        },

        eventDragStart: function (info) {
            document.querySelectorAll('.event-tooltip').forEach(tt => tt.remove());
        },

        eventDrop: async function (info) {
            document.querySelectorAll('.event-tooltip').forEach(tt => tt.remove());

            try {
                const newStart = info.event.start.toISOString();
                await updateEventTime(info.event.id, newStart);
                showNotification('Event time updated!', 'success');
            } catch (error) {
                info.revert();
                showNotification('Failed to update: ' + error.message, 'error');
            }
        },

        eventResize: async function (info) {
            try {
                const newDuration = Math.round((info.event.end - info.event.start) / 60000);
                // We need to update the event duration in the backend
                // Currently updateEventTime supports duration, so we can use it
                // But we need the start time too
                const start = info.event.start.toISOString();
                await updateEventTime(info.event.id, start, newDuration);

                showNotification('Event duration adjusted!', 'success');
            } catch (error) {
                info.revert();
                showNotification('Failed to resize: ' + error.message, 'error');
            }
        },

        eventClick: function (info) {
            console.log('Event clicked - use double-click to edit');
        }
    });

    calendar.render();
    console.log('Calendar rendered - DOUBLE-CLICK events to edit time');
}

function transformEventsToCalendar(events) {
    return events.map(event => {
        const start = new Date(event.timestamp_start);
        const end = new Date(start.getTime() + event.duration_minutes * 60000);

        const stateClass = event.key_state ?
            'event-' + event.key_state.toLowerCase().replace(/\s+/g, '-').replace('internal-friction', 'friction') :
            'event-routine';

        return {
            id: event.event_id,
            title: event.activity + (event.energy_cost ? ` (${event.energy_cost >= 0 ? '+' : ''}${event.energy_cost})` : ''),
            start: start,
            end: end,
            className: stateClass,
            extendedProps: {
                goal_name: event.goal_name,
                key_state: event.key_state,
                energy_cost: event.energy_cost,
                duration_minutes: event.duration_minutes,
                physical_score: event.physical_score,
                mental_score: event.mental_score,
                emotional_score: event.emotional_score,
                notes: event.notes
            }
        };
    });
}

function updateCalendarEvents(events) {
    if (!calendar) return;
    const calendarEvents = transformEventsToCalendar(events);
    calendar.removeAllEvents();
    calendar.addEventSource(calendarEvents);
}

function changeCalendarView(viewName, buttonEl) {
    if (!calendar) return;

    document.querySelectorAll('.view-btn').forEach(btn => btn.classList.remove('active'));
    if (buttonEl) buttonEl.classList.add('active');

    calendar.changeView(viewName);
}

async function updateEventTime(eventId, newTimestamp, newDuration = null) {
    console.log('Updating event', eventId, 'to', newTimestamp, 'duration:', newDuration);

    const payload = { timestamp_start: newTimestamp };
    if (newDuration !== null) {
        payload.duration_minutes = newDuration;
    }

    const response = await fetch(`${API_BASE}/api/events/${eventId}/time`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    if (!response.ok) throw new Error('Failed to update event time');
    return await response.json();
}

// Override removed - logic is now in app.js

// Override logEvent
if (typeof logEvent !== 'undefined') {
    const originalLogEvent = logEvent;
    logEvent = async function (event) {
        event.preventDefault();

        const dateValue = document.getElementById('event-date').value;
        const timeValue = document.getElementById('event-time').value;
        const timestamp = new Date(`${dateValue}T${timeValue}`).toISOString();

        const eventData = {
            activity: document.getElementById('event-activity').value,
            duration_minutes: parseInt(document.getElementById('event-duration').value),
            goal_id: document.getElementById('event-goal').value || null,
            key_state: document.getElementById('event-state').value,
            physical_score: parseInt(document.getElementById('event-physical').value),
            mental_score: parseInt(document.getElementById('event-mental').value),
            emotional_score: parseInt(document.getElementById('event-emotional').value),
            notes: document.getElementById('event-notes').value,
            timestamp_start: timestamp
        };

        try {
            await createEvent(eventData);
            closeModal('log-event-modal');
            document.getElementById('log-event-form').reset();
            if (currentPage === 'journal') {
                await loadJournal(90);
            }
            showNotification('Event logged successfully!', 'success');
        } catch (error) {
            showNotification('Error: ' + error.message, 'error');
        }
    };
}

console.log('calendar.js loaded - Use DOUBLE-CLICK to edit event times (custom dialog)');
