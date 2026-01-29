document.addEventListener('DOMContentLoaded', async function () {
    // --- Toast Notification System ---
    window.showToast = function (options) {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const {
            type = 'info',      // 'success', 'error', 'warning', 'info'
            title = '',
            message = '',
            duration = 3000,
            showProgress = true,
            closable = true
        } = options;

        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        // Icon SVG based on type
        const icons = {
            success: '<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2.5" fill="none"><polyline points="20 6 9 17 4 12"></polyline></svg>',
            error: '<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2.5" fill="none"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
            warning: '<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2.5" fill="none"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
            info: '<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2.5" fill="none"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'
        };

        let html = `
            <div class="toast-icon">${icons[type] || icons.info}</div>
            <div class="toast-content">
        `;

        if (title) {
            html += `<div class="toast-title">${title}</div>`;
        }
        if (message) {
            html += `<div class="toast-message">${message}</div>`;
        }

        html += `</div>`;

        if (closable) {
            html += `
                <button class="toast-close" onclick="this.parentElement.remove()">
                    <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            `;
        }

        if (showProgress) {
            html += `<div class="toast-progress" style="animation-duration: ${duration}ms"></div>`;
        }

        toast.innerHTML = html;
        container.appendChild(toast);

        // Auto remove after duration
        if (duration > 0) {
            setTimeout(() => {
                toast.classList.add('toast-removing');
                toast.addEventListener('animationend', () => {
                    toast.remove();
                });
            }, duration);
        }

        return toast;
    };

    // Convenience methods
    window.toastSuccess = (message, title = '成功') => showToast({ type: 'success', title, message });
    window.toastError = (message, title = '错误') => showToast({ type: 'error', title, message, duration: 4000 });
    window.toastWarning = (message, title = '警告') => showToast({ type: 'warning', title, message });
    window.toastInfo = (message, title = '提示') => showToast({ type: 'info', title, message });

    function loadExternalScript(url, timeoutMs = 4500) {
        return new Promise((resolve, reject) => {
            const s = document.createElement('script');
            const timer = setTimeout(() => {
                try {
                    s.remove();
                } catch (e) { }
                reject(new Error('timeout'));
            }, timeoutMs);
            s.src = url;
            s.async = true;
            s.onload = () => {
                clearTimeout(timer);
                resolve(true);
            };
            s.onerror = () => {
                clearTimeout(timer);
                reject(new Error('failed_to_load'));
            };
            document.head.appendChild(s);
        });
    }

    async function ensureGlobal(checkFn, urls) {
        try {
            if (checkFn()) return true;
        } catch (e) { }
        for (const url of urls) {
            try {
                await loadExternalScript(url);
                if (checkFn()) return true;
            } catch (e) { }
        }
        return false;
    }

    window.toggleSidebar = window.toggleSidebar || function () {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.querySelector('.sidebar-overlay');
        if (!sidebar || !overlay) return;
        const isMobile = window.innerWidth < 1024;
        if (isMobile) {
            sidebar.classList.toggle('mobile-open');
            if (sidebar.classList.contains('mobile-open')) {
                overlay.classList.add('active');
            } else {
                overlay.classList.remove('active');
            }
        } else {
            sidebar.classList.toggle('closed');
        }
    };

    window.closeSidebar = window.closeSidebar || function () {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.querySelector('.sidebar-overlay');
        if (!sidebar || !overlay) return;
        sidebar.classList.remove('mobile-open');
        overlay.classList.remove('active');
    };

    window.switchTab = window.switchTab || function () {
        toastInfo('页面还在加载中，请稍等一下');
    };

    window.showAddModal = window.showAddModal || function () {
        toastInfo('页面还在加载中，请稍等一下');
    };

    window.showAddStudentModal = window.showAddStudentModal || function () {
        toastInfo('页面还在加载中，请稍等一下');
    };

    await ensureGlobal(
        () => typeof window.marked !== 'undefined' && window.marked && typeof window.marked.Renderer === 'function',
        [
            'https://cdn.jsdelivr.net/npm/marked/marked.min.js',
            'https://unpkg.com/marked/marked.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/marked/13.0.2/marked.min.js'
        ]
    );

    if (typeof window.marked !== 'undefined' && window.marked && typeof window.marked.Renderer === 'function') {
        const renderer = new window.marked.Renderer();
        renderer.hr = () => '';
        window.marked.setOptions({ renderer, breaks: true });
    }

    (function () {
        const AUTH_STORAGE_KEY = 'teacher_auth_v1';
        const AUTH_TTL_MS = 1000 * 60 * 60 * 24 * 30;
        const AUTH_PASSWORD = '0718';

        const modal = document.getElementById('authModal');
        const input = document.getElementById('authPassword');
        const submitBtn = document.getElementById('authSubmitBtn');
        const clearBtn = document.getElementById('authClearBtn');
        const content = modal ? modal.querySelector('.auth-modal-content') : null;

        const readAuth = () => {
            try {
                const raw = localStorage.getItem(AUTH_STORAGE_KEY);
                if (!raw) return null;
                return JSON.parse(raw);
            } catch (e) {
                return null;
            }
        };

        const isAuthed = () => {
            const data = readAuth();
            if (!data || !data.ok || !data.ts) return false;
            return Date.now() - data.ts < AUTH_TTL_MS;
        };

        const lock = () => {
            document.body.classList.add('auth-locked');
            if (modal) modal.style.display = 'flex';
            if (input) {
                input.value = '';
                setTimeout(() => input.focus(), 50);
            }
        };

        const unlock = () => {
            document.body.classList.remove('auth-locked');
            if (modal) modal.style.display = 'none';
        };

        const shake = () => {
            if (!content) return;
            content.classList.remove('shake');
            void content.offsetWidth;
            content.classList.add('shake');
        };

        const submit = () => {
            const v = (input ? input.value : '').trim();
            if (v === AUTH_PASSWORD) {
                localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ ok: true, ts: Date.now() }));
                unlock();
                toastSuccess('已通过验证，欢迎回来', '你好呀');
                return;
            }
            shake();
            if (input) input.value = '';
            toastError('密码不对，再试一次吧', '验证失败');
            if (input) input.focus();
        };

        if (!modal || !input || !submitBtn || !clearBtn) return;

        submitBtn.addEventListener('click', submit);
        clearBtn.addEventListener('click', () => {
            input.value = '';
            input.focus();
        });
        input.addEventListener('input', () => {
            input.value = input.value.replace(/\D/g, '').slice(0, 4);
            if (input.value.length === 4) {
                submit();
            }
        });
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                submit();
            }
        });

        if (isAuthed()) {
            unlock();
        } else {
            lock();
        }
    })();

    // --- Student Color Management ---
    // 为每个学生分配固定的颜色，便于识别
    var studentColors = JSON.parse(localStorage.getItem('studentColors') || '{}');

    // 预定义的颜色方案（柔和的糖果色系）
    var colorPalette = [
        { primary: '#ED0D92', light: '#FFF0F5', name: '樱花粉' },      // 原主色
        { primary: '#FF6B9D', light: '#FFF0F5', name: '蜜桃粉' },
        { primary: '#9B59B6', light: '#F5EEF8', name: '薰衣草' },
        { primary: '#3498DB', light: '#EBF5FB', name: '天空蓝' },
        { primary: '#1ABC9C', light: '#E8F8F5', name: '薄荷绿' },
        { primary: '#F39C12', light: '#FEF5E7', name: '橘子橙' },
        { primary: '#E74C3C', light: '#FDEDEC', name: '草莓红' },
        { primary: '#2ECC71', light: '#E8F8F0', name: '青草绿' },
        { primary: '#F1C40F', light: '#FEF9E7', name: '柠檬黄' },
        { primary: '#E91E63', light: '#FCE4EC', name: '玫瑰红' },
        { primary: '#673AB7', light: '#EDE7F6', name: '紫罗兰' },
        { primary: '#00BCD4', light: '#E0F7FA', name: '青蓝色' },
        { primary: '#FF9800', light: '#FFF3E0', name: '杏子橙' },
        { primary: '#4CAF50', light: '#E8F5E9', name: '森林绿' },
        { primary: '#FF5722', light: '#FBE9E7', name: '珊瑚橙' }
    ];

    // 获取学生颜色（如果不存在则分配新颜色）
    function getStudentColor(studentName) {
        if (!studentName) return colorPalette[0];

        if (!studentColors[studentName]) {
            // 获取已使用的颜色索引
            var usedIndices = Object.values(studentColors).map(c => c.index);
            // 找到第一个未使用的颜色
            var availableIndex = colorPalette.findIndex((_, i) => !usedIndices.includes(i));
            // 如果所有颜色都用完了，循环使用
            if (availableIndex === -1) {
                availableIndex = Object.keys(studentColors).length % colorPalette.length;
            }
            studentColors[studentName] = {
                index: availableIndex,
                primary: colorPalette[availableIndex].primary,
                light: colorPalette[availableIndex].light,
                name: colorPalette[availableIndex].name
            };
            // 保存到本地存储
            localStorage.setItem('studentColors', JSON.stringify(studentColors));
        }
        return studentColors[studentName];
    }

    function escapeHtml(text) {
        return String(text ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatHHMM(date) {
        if (!date) return '';
        return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false });
    }

    function getResponsiveView(requestedView) {
        const isMobile = window.innerWidth < 768;
        if (requestedView === 'timeGridWeek' && isMobile) return 'listWeek';
        return requestedView;
    }

    function syncCalendarViewButtons(viewType) {
        const viewButtons = document.querySelectorAll('.view-btn');
        viewButtons.forEach(function (b) { b.classList.remove('active'); });
        const normalized = viewType === 'listWeek' ? 'timeGridWeek' : viewType;
        const matched = document.querySelector(`.view-btn[data-view="${normalized}"]`);
        if (matched) matched.classList.add('active');
    }

    function updateCalendarTitle(date, viewType) {
        const titleEl = document.getElementById('calendarTitle');
        if (!titleEl || !date) return;

        const year = date.getFullYear();
        const month = date.getMonth() + 1;
        const day = date.getDate();
        const isCompact = window.innerWidth < 480;

        let titleText = '';
        if (viewType === 'dayGridMonth') {
            titleText = `${year}年${month}月`;
        } else if (viewType === 'timeGridWeek' || viewType === 'listWeek') {
            const weekEnd = new Date(date);
            weekEnd.setDate(weekEnd.getDate() + 6);
            const endMonth = weekEnd.getMonth() + 1;
            const endDay = weekEnd.getDate();
            if (isCompact) {
                titleText = `${month}/${day}-${endMonth}/${endDay}`;
            } else if (month === endMonth) {
                titleText = `${year}年${month}月${day}日-${endDay}日`;
            } else {
                titleText = `${year}年${month}月${day}日-${endMonth}月${endDay}日`;
            }
        } else if (viewType === 'timeGridDay') {
            const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
            if (isCompact) {
                titleText = `${month}月${day}日 ${weekdays[date.getDay()]}`;
            } else {
                titleText = `${year}年${month}月${day}日 ${weekdays[date.getDay()]}`;
            }
        }

        titleEl.textContent = titleText;
    }

    // 重置学生颜色（用于测试）
    window.resetStudentColors = function () {
        studentColors = {};
        localStorage.removeItem('studentColors');
        if (calendar) {
            calendar.refetchEvents();
        }
        toastSuccess('学生颜色已重置');
    };

    // --- Calendar Initialization ---
    var calendarEl = document.getElementById('calendar');

    // Determine initial view based on screen width
    var initialView = window.innerWidth < 768 ? 'timeGridDay' : 'dayGridMonth';

    var calendar = null;

    const calendarReady = await ensureGlobal(
        () => typeof window.FullCalendar !== 'undefined' && window.FullCalendar && typeof window.FullCalendar.Calendar === 'function',
        [
            'https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/index.global.min.js',
            'https://unpkg.com/fullcalendar@6.1.10/index.global.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/fullcalendar/6.1.19/index.global.min.js'
        ]
    );

    if (!calendarReady || !calendarEl) {
        if (!calendarReady) {
            toastError('日历组件加载失败，请检查网络后刷新页面', '加载失败');
        }
    } else {
        calendar = new window.FullCalendar.Calendar(calendarEl, {
        initialView: initialView,
        headerToolbar: false, // 隐藏默认工具栏
        locale: 'zh-cn',
        windowResize: function () {
            const isMobile = window.innerWidth < 768;
            const currentView = calendar.view.type;
            if (isMobile && currentView === 'dayGridMonth') {
                calendar.changeView('timeGridDay');
            } else if (!isMobile && currentView === 'timeGridDay') {
                calendar.changeView('dayGridMonth');
            }
            if (isMobile && currentView === 'timeGridWeek') {
                calendar.changeView('listWeek');
            } else if (!isMobile && currentView === 'listWeek') {
                calendar.changeView('timeGridWeek');
            }
        },
        allDaySlot: false,
        slotMinTime: '08:00:00',
        slotMaxTime: '22:00:00',
        expandRows: true,
        height: '100%',
        nowIndicator: true, // 显示当前时间指示器
        events: '/api/courses', // Fetch from backend
        eventContent: function (arg) {
            const viewType = arg.view?.type || '';
            const isMobile = window.innerWidth < 768;
            if (!isMobile) return true;

            const title = arg.event.title || '未命名课程';
            const props = arg.event.extendedProps || {};
            const studentName = props.student_name || '';
            const location = props.location || '';
            const price = props.price;
            const durationMinutes = (arg.event.end && arg.event.start)
                ? Math.max(0, Math.round((arg.event.end.getTime() - arg.event.start.getTime()) / 60000))
                : 0;

            const startText = formatHHMM(arg.event.start);
            const endText = formatHHMM(arg.event.end);
            const timeRangeText = startText && endText ? `${startText}-${endText}` : (arg.timeText || '');

            const showStudent = Boolean(studentName) && durationMinutes >= 45;
            const showLocation = Boolean(location) && durationMinutes >= 90;
            const showTime = durationMinutes >= 35;

            const titleLine = showStudent ? `${title} · ${studentName}` : title;
            const listTitleLine = studentName ? `${title} · ${studentName}` : title;

            const metaParts = [];
            if (showTime && timeRangeText) {
                metaParts.push(`<span class="mobile-event-time-pill fc-event-time">${escapeHtml(timeRangeText)}</span>`);
            }
            if (showLocation) {
                metaParts.push(`<span class="mobile-event-location">${escapeHtml(location)}</span>`);
            }

            if (viewType === 'listWeek') {
                const listMetaParts = [];
                if (timeRangeText) {
                    listMetaParts.push(`<span class="mobile-event-time-pill fc-event-time">${escapeHtml(timeRangeText)}</span>`);
                }
                if (location) {
                    listMetaParts.push(`<span class="mobile-event-location">${escapeHtml(location)}</span>`);
                }
                if (price) {
                    const p = Number(price);
                    if (Number.isFinite(p) && p > 0) {
                        listMetaParts.push(`<span class="mobile-event-price">¥${escapeHtml(p.toFixed(0))}</span>`);
                    }
                }
                return {
                    html: `
                        <div class="mobile-list-event">
                            <div class="mobile-list-title">${escapeHtml(listTitleLine)}</div>
                            ${listMetaParts.length ? `<div class="mobile-event-meta">${listMetaParts.join('')}</div>` : ''}
                        </div>
                    `
                };
            }

            if (!viewType.startsWith('timeGrid')) return true;
            return {
                html: `
                    <div class="mobile-event-content">
                        <div class="mobile-event-title fc-event-title">${escapeHtml(titleLine)}</div>
                        ${metaParts.length ? `<div class="mobile-event-meta">${metaParts.join('')}</div>` : ''}
                    </div>
                `
            };
        },

        // --- Interactive Features ---
        editable: true,       // Allow drag & drop + resize
        droppable: true,
        eventDurationEditable: true,

        // --- Update custom title when dates change ---
        datesSet: function (info) {
            updateCalendarTitle(info.view.currentStart, info.view.type);
            syncCalendarViewButtons(info.view.type);
        },

        // --- Conflict Visualization & Student Color ---
        eventDidMount: function (info) {
            const current = info.event;
            const props = current.extendedProps;
            const isDesktop = window.innerWidth >= 1024;
            const viewType = info.view?.type || '';

            // 应用学生颜色
            const studentName = props.student_name;
            const price = props.price;
            const colorInfo = getStudentColor(studentName);

            if (viewType === 'listWeek') {
                const listDot = info.el.querySelector('.fc-list-event-dot');
                if (listDot) {
                    listDot.style.borderColor = colorInfo.primary;
                    listDot.style.backgroundColor = colorInfo.primary;
                }

                const listTitleLink = info.el.querySelector('.fc-list-event-title a');
                if (listTitleLink) {
                    listTitleLink.style.borderLeft = `4px solid ${colorInfo.primary}`;
                    listTitleLink.style.borderRadius = '10px';
                    listTitleLink.style.paddingLeft = '10px';
                }
            }

            const eventMain = info.el.querySelector('.fc-event-main');
            if (eventMain) {
                eventMain.style.borderLeftColor = colorInfo.primary;
                eventMain.style.background = `linear-gradient(135deg, ${colorInfo.light} 0%, #FFFFFF 100%)`;

                const titleEl = info.el.querySelector('.fc-event-title');
                if (titleEl) {
                    titleEl.style.color = colorInfo.primary;
                }

                // 桌面端：添加额外的课程信息
                if (isDesktop) {
                    eventMain.classList.add('desktop-event');

                    // 创建或更新桌面端详细信息区域
                    let extraInfo = eventMain.querySelector('.event-extra-info');
                    if (!extraInfo) {
                        extraInfo = document.createElement('div');
                        extraInfo.className = 'event-extra-info';
                        eventMain.appendChild(extraInfo);
                    }

                    // 构建额外信息HTML
                    let extraHtml = '';
                    if (studentName) {
                        extraHtml += `<span class="event-student-name">
                            <svg viewBox="0 0 16 16" width="12" height="12">
                                <circle cx="8" cy="5" r="3" fill="currentColor"/>
                                <path d="M2 15c0-3 2-5 6-5s6 2 6 5" fill="none" stroke="currentColor" stroke-width="1.5"/>
                            </svg>
                            ${studentName}
                        </span>`;
                    }
                    if (price) {
                        extraHtml += `<span class="event-price">¥${Number(price).toFixed(0)}</span>`;
                    }
                    extraInfo.innerHTML = extraHtml;
                } else {
                    // 移动端：移除额外信息
                    const extraInfo = eventMain.querySelector('.event-extra-info');
                    if (extraInfo) {
                        extraInfo.remove();
                    }
                }
            }

            // Check for overlaps
            const events = calendar.getEvents();
            const hasConflict = events.some(e => {
                if (e.id === current.id) return false;
                return (current.start < e.end && current.end > e.start);
            });

            if (hasConflict) {
                info.el.classList.add('conflict-event');
            }
        },

        // --- Event Handlers ---
        eventClick: function (info) {
            currentEventId = info.event.id;
            showEditModal(info.event);
        },

        eventDrop: async function (info) {
            await handleEventUpdate(info);
        },

        eventResize: async function (info) {
            await handleEventUpdate(info);
        }
        });
    }

    const viewButtons = document.querySelectorAll('.view-btn');
    if (calendar) {
        viewButtons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                const view = this.getAttribute('data-view');
                if (!view) return;
                calendar.changeView(getResponsiveView(view));
                syncCalendarViewButtons(calendar.view.type);
            });
        });
    }

    // Helper to sync drag/resize to backend
    async function handleEventUpdate(info) {
        const event = info.event;
        const props = event.extendedProps;

        // Optimistic UI: It already moved on screen.
        // We just need to save. If fail, revert.

        try {
            const res = await fetch(`/api/courses/${event.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: event.title,
                    student_id: props.student_id,
                    start: event.start.toISOString(),
                    end: event.end.toISOString(),
                    price: props.price
                })
            });

            if (!res.ok) {
                throw new Error('Save failed');
            }
            // Success: show toast
            toastSuccess('课程已更新');
            // Re-render to update conflict styles if any moved
            if (calendar) {
                calendar.render();
            }

        } catch (e) {
            toastError('保存失败，正在还原...');
            info.revert();
        }
    }
    if (calendar) {
        calendar.render();
    }

    // --- Custom Calendar Header Functions ---

    // Navigation buttons
    const prevBtn = document.getElementById('prevMonth');
    const nextBtn = document.getElementById('nextMonth');
    if (calendar) {
        if (prevBtn) {
            prevBtn.addEventListener('click', function () {
                calendar.prev();
            });
        }
        if (nextBtn) {
            nextBtn.addEventListener('click', function () {
                calendar.next();
            });
        }
        updateCalendarTitle(calendar.view.currentStart, calendar.view.type);
        syncCalendarViewButtons(calendar.view.type);
    }

    let calendarTitleResizeTimer = null;
    window.addEventListener('resize', () => {
        if (calendarTitleResizeTimer) clearTimeout(calendarTitleResizeTimer);
        calendarTitleResizeTimer = setTimeout(() => {
            if (calendar) {
                updateCalendarTitle(calendar.view.currentStart, calendar.view.type);
            }
        }, 150);
    });

    // --- Sidebar Toggle ---
    window.toggleSidebar = function () {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.querySelector('.sidebar-overlay');
        const isMobile = window.innerWidth < 1024;

        if (isMobile) {
            sidebar.classList.toggle('mobile-open');
            // Check if open to show overlay
            if (sidebar.classList.contains('mobile-open')) {
                overlay.classList.add('active'); // We need CSS for this or just rely on sidebar css
            } else {
                overlay.classList.remove('active');
            }
        } else {
            sidebar.classList.toggle('closed');
            // Trigger calendar resize because main content width changed
            setTimeout(() => {
                if (calendar) {
                    calendar.updateSize();
                }
            }, 300);
        }
    }

    window.closeSidebar = function () {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.querySelector('.sidebar-overlay');
        sidebar.classList.remove('mobile-open');
        overlay.classList.remove('active');
    }

    // --- Chat Logic ---
    const chatInput = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('messages');
    let currentThreadId = 'thread-' + Date.now();

    window.startNewChat = function () {
        showConfirmModal({
            title: '开始新对话',
            message: '确定要开始新的对话吗？',
            detail: '当前对话内容会清空。',
            confirmText: '开始',
            cancelText: '取消',
            danger: false
        }).then((confirmed) => {
            if (!confirmed) return;
            currentThreadId = 'thread-' + Date.now();
            messagesContainer.innerHTML = `
                <div class="message ai-message">
                    <div class="message-content">
                        你好！我是你的课程助理，请问今天有什么安排？
                    </div>
                </div>
            `;
            toastInfo('已开始新会话');
        });
    };

    window.adjustTextareaHeight = function (el) {
        el.style.height = 'auto';
        el.style.height = (el.scrollHeight) + 'px';
    }

    window.handleEnter = function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    }

    // 发送消息并处理重试逻辑
    window.sendMessage = async function (retryCount = 0, originalText = null) {
        const text = originalText || chatInput.value.trim();
        if (!text) return;

        // 首次调用时添加用户消息
        if (retryCount === 0) {
            appendMessage(text, 'user-message');
            chatInput.value = '';
            chatInput.style.height = 'auto';
        }

        // Add AI Placeholder (只首次创建)
        let aiMessageDiv, contentDiv;
        if (retryCount === 0) {
            aiMessageDiv = appendMessage('', 'ai-message');
            contentDiv = aiMessageDiv.querySelector('.message-content');
            contentDiv.innerHTML = '<span class="typing">...</span>';
        } else {
            // 重试时获取最后一个 AI 消息
            const lastAiMsg = messagesContainer.querySelector('.message.ai-message:last-of-type');
            if (lastAiMsg) {
                aiMessageDiv = lastAiMsg;
                contentDiv = aiMessageDiv.querySelector('.message-content');
            }
        }
        if (!aiMessageDiv || !contentDiv) return;

        // Remove typing indicator on first chunk
        let isFirstChunk = true;
        let accumulatedText = '';
        let activeTools = [];
        let toolsHistory = [];
        let suppressTokensUntilDone = false;
        let toolIconPaths = {};
        const TOOL_ICONS = {
            default: "M10 2c-4.42 0-8 3.58-8 8s3.58 8 8 8 8-3.58 8-8-3.58-8-8-8zm0 14.5c-3.59 0-6.5-2.91-6.5-6.5S6.41 3.5 10 3.5s6.5 2.91 6.5 6.5-2.91 6.5-6.5 6.5zm.5-10.5h-1v5l4.25 2.5.75-1.23-3.5-2.08V6z",
            search: "M12.9 14.32a8 8 0 1 1 1.41-1.41l5.35 5.33-1.42 1.42-5.33-5.35zM8 14a6 6 0 1 0 0-12 6 6 0 0 0 0 12z",
            write: "M13.5 3c.28 0 .5.22.5.5v13a.5.5 0 0 1-1 0v-13c0-.28.22-.5.5-.5zM6 6.5a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1-.5-.5zm0 4a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1-.5-.5zm0 4a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1-.5-.5z",
            add: "M10 4a1 1 0 0 1 1 1v4h4a1 1 0 1 1 0 2h-4v4a1 1 0 1 1-2 0v-4H5a1 1 0 1 1 0-2h4V5a1 1 0 0 1 1-1z",
            delete: "M15 4V3H5v1H3v2h14V4h-2zm1 4H4v11a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V8zM6 16v-6h1.5v6H6zm3.5 0v-6H11v6H9.5zm3.5 0v-6h1.5v6H13z",
            calc: "M4 3a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H4zm0 2h12v3H4V5zm0 5h3v2H4v-2zm5 0h3v2H9v-2zm5 0h2v2h-2v-2zm-5 4h3v2H9v-2zm-5 0h3v2H4v-2zm10 0h2v2h-2v-2z",
            check: "M7.25 12.25L9.5 14.5 15.5 8.5"
        };

        function stripLeakedToolJson(text, enabled) {
            if (!enabled || !text) return text;

            const isLikelyToolData = (val) => {
                const toolKeys = new Set([
                    'id', 'student_id', 'student_name', 'student_grade',
                    'phone', 'parent_contact', 'progress', 'notes',
                    'title', 'start', 'end', 'location', 'price', 'color',
                    'description'
                ]);

                const scoreObject = (obj) => {
                    if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return 0;
                    let score = 0;
                    for (const k of Object.keys(obj)) {
                        if (toolKeys.has(k)) score++;
                    }
                    return score;
                };

                if (Array.isArray(val)) {
                    if (val.length === 0) return true;
                    const head = val[0];
                    if (head && typeof head === 'object' && !Array.isArray(head)) {
                        return scoreObject(head) >= 2;
                    }
                    return false;
                }

                if (val && typeof val === 'object') {
                    return scoreObject(val) >= 3;
                }

                return false;
            };

            const findJsonEnd = (s, startIdx) => {
                const first = s[startIdx];
                if (first !== '{' && first !== '[') return -1;
                const stack = [first === '{' ? '}' : ']'];
                let inStr = false;
                let esc = false;
                for (let i = startIdx + 1; i < s.length; i++) {
                    const ch = s[i];
                    if (inStr) {
                        if (esc) {
                            esc = false;
                            continue;
                        }
                        if (ch === '\\') {
                            esc = true;
                            continue;
                        }
                        if (ch === '"') {
                            inStr = false;
                        }
                        continue;
                    }

                    if (ch === '"') {
                        inStr = true;
                        continue;
                    }

                    if (ch === '{') {
                        stack.push('}');
                        continue;
                    }
                    if (ch === '[') {
                        stack.push(']');
                        continue;
                    }
                    if (stack.length && ch === stack[stack.length - 1]) {
                        stack.pop();
                        if (stack.length === 0) return i;
                    }
                }
                return -1;
            };

            let out = '';
            for (let i = 0; i < text.length;) {
                const ch = text[i];
                if (ch === '{' || ch === '[') {
                    const end = findJsonEnd(text, i);
                    if (end !== -1) {
                        const candidate = text.slice(i, end + 1);
                        if (candidate.length <= 20000) {
                            try {
                                const parsed = JSON.parse(candidate);
                                if (isLikelyToolData(parsed)) {
                                    i = end + 1;
                                    continue;
                                }
                            } catch (e) { }
                        }
                    }
                }
                out += ch;
                i++;
            }

            return out
                .replace(/\n\s*\n\s*\n+/g, '\n\n')
                .replace(/^\s*\[\s*\]\s*$/gm, '')
                .trim();
        }

        function ensureToolHatToggle(toolHat) {
            const toggle = () => {
                if (toolHat.classList.contains('collapsed')) {
                    toolHat.classList.remove('collapsed');
                    toolHat.classList.add('expanded');
                    toolHat.setAttribute('aria-expanded', 'true');
                } else {
                    toolHat.classList.remove('expanded');
                    toolHat.classList.add('collapsed');
                    toolHat.setAttribute('aria-expanded', 'false');
                }
            };

            toolHat.addEventListener('click', toggle);
            toolHat.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    toggle();
                }
            });
        }

        function lockToolHat(toolHat) {
            const count = toolsHistory.length;
            toolHat.classList.remove('hiding');
            toolHat.classList.add('locked', 'collapsed');
            toolHat.setAttribute('role', 'button');
            toolHat.setAttribute('tabindex', '0');
            toolHat.setAttribute('aria-expanded', 'false');

            const itemsHtml = toolsHistory.map((t, idx) => {
                const iconPath = t.iconPath || TOOL_ICONS.default;
                return `
                    <div class="tool-hat-item">
                        <div class="tool-hat-item-index">${idx + 1}</div>
                        <div class="tool-hat-item-icon">
                            <svg viewBox="0 0 20 20" width="14" height="14" fill="currentColor">
                                <path d="${iconPath}"></path>
                            </svg>
                        </div>
                        <div class="tool-hat-item-name">${escapeHtml(t.name || '')}</div>
                    </div>
                `;
            }).join('');

            toolHat.innerHTML = `
                <div class="tool-hat-row">
                    <div class="tool-hat-icon">
                        <svg viewBox="0 0 20 20" width="14" height="14" fill="currentColor">
                            <path d="${TOOL_ICONS.check}"></path>
                        </svg>
                    </div>
                    <div class="tool-hat-text">工具调用完成 · 共 ${count} 个（点开查看）</div>
                    <div class="tool-hat-toggle" aria-hidden="true">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M6 9l6 6 6-6"></path>
                        </svg>
                    </div>
                </div>
                <div class="tool-hat-details">
                    ${itemsHtml}
                </div>
            `;

            if (!toolHat.dataset.boundToggle) {
                toolHat.dataset.boundToggle = '1';
                ensureToolHatToggle(toolHat);
            }
        }

        try {
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, thread_id: currentThreadId })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // 检查响应类型，如果是 HTML 或者是明显的非 JSON 类型则抛出错误
            const contentType = response.headers.get('content-type') || '';
            if (contentType.includes('text/html')) {
                throw new Error('服务器返回了错误页面 (HTML)，请检查后端服务是否正常运行');
            }

            // 允许 application/json 和 text/plain (有时流式响应会被识别为 text/plain)
            if (!contentType.includes('application/json') && !contentType.includes('text/plain')) {
                console.warn('Unexpected content-type:', contentType);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");

            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;

                // Process buffer by lines
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Keep incomplete line in buffer

                for (const line of lines) {
                    if (!line.trim()) continue;

                    // 检查是否是错误响应（非 JSON）
                    if (line.includes('AI Service') || line.includes('error') || line.includes('Error')) {
                        throw new Error('AI 服务暂时不可用');
                    }

                    try {
                        const data = JSON.parse(line);

                        if (isFirstChunk && data.type !== 'token') {
                            contentDiv.innerHTML = '';
                            const mdBody = document.createElement('div');
                            mdBody.className = 'markdown-body';
                            contentDiv.appendChild(mdBody);
                            isFirstChunk = false;
                        }

                        if (data.type === 'token') {
                            if (suppressTokensUntilDone) {
                                continue;
                            }

                            accumulatedText += data.content;

                            if (isFirstChunk) {
                                contentDiv.innerHTML = '';
                                const mdBody = document.createElement('div');
                                mdBody.className = 'markdown-body';
                                contentDiv.appendChild(mdBody);
                                isFirstChunk = false;
                            }

                            let mdBody = contentDiv.querySelector('.markdown-body');
                            if (!mdBody) {
                                mdBody = document.createElement('div');
                                mdBody.className = 'markdown-body';
                                contentDiv.appendChild(mdBody);
                            }

                            const renderText = accumulatedText
                                .split('\u0000').join('')
                                .split('\u0001').join('')
                                .split('\u0002').join('')
                                .split('\u0003').join('')
                                .split('\u0004').join('')
                                .split('\u0005').join('')
                                .split('\u0006').join('')
                                .split('\u0007').join('')
                                .split('\u0008').join('')
                                .split('\u000b').join('')
                                .split('\u000c').join('')
                                .split('\u000e').join('')
                                .split('\u000f').join('')
                                .split('\u0010').join('')
                                .split('\u0011').join('')
                                .split('\u0012').join('')
                                .split('\u0013').join('')
                                .split('\u0014').join('')
                                .split('\u0015').join('')
                                .split('\u0016').join('')
                                .split('\u0017').join('')
                                .split('\u0018').join('')
                                .split('\u0019').join('')
                                .split('\u001a').join('')
                                .split('\u001b').join('')
                                .split('\u001c').join('')
                                .split('\u001d').join('')
                                .split('\u001e').join('')
                                .split('\u001f').join('')
                                .replace(/\r\n/g, '\n')
                                .replace(/\r/g, '\n');
                            const safeText = stripLeakedToolJson(renderText, toolsHistory.length > 0);
                            const finalText = safeText
                                .replace(/^[\t ]*[━─—\-_=]{8,}[\t ]*$/gm, '')
                                .replace(/\n{3,}/g, '\n\n');

                            if (typeof marked !== 'undefined') {
                                mdBody.innerHTML = marked.parse(finalText);
                            } else {
                                mdBody.textContent = finalText;
                            }

                        } else if (data.type === 'tool_start' || data.type === 'tool') {
                            const toolName = data.name;
                            suppressTokensUntilDone = true;

                            let mdBody = contentDiv.querySelector('.markdown-body');
                            if (mdBody) {
                                mdBody.innerHTML = '';
                            }

                            // Determine icon based on keywords
                            let iconPath = TOOL_ICONS.default;
                            if (toolName.includes("翻阅") || toolName.includes("查找") || toolName.includes("获取")) iconPath = TOOL_ICONS.search;
                            if (toolName.includes("创建") || toolName.includes("更新") || toolName.includes("安排") || toolName.includes("修改")) iconPath = TOOL_ICONS.write;
                            if (toolName.includes("移除") || toolName.includes("删除")) iconPath = TOOL_ICONS.delete;
                            if (toolName.includes("计算") || toolName.includes("统计") || toolName.includes("生成") || toolName.includes("分析")) iconPath = TOOL_ICONS.calc;
                            if (toolName.includes("检查")) iconPath = TOOL_ICONS.check;
                            toolIconPaths[toolName] = iconPath;
                            activeTools.push(toolName);
                            toolsHistory.push({ name: toolName, iconPath });

                            // --- 1. Tool Hat Logic (Hello Kitty Style) ---
                            let toolHat = contentDiv.querySelector('.tool-hat');
                            if (!toolHat) {
                                toolHat = document.createElement('div');
                                toolHat.className = 'tool-hat';
                                // Prepend to contentDiv so it sits at the top
                                contentDiv.insertBefore(toolHat, contentDiv.firstChild);
                            }
                            if (toolHat.classList.contains('locked')) {
                                toolHat.className = 'tool-hat';
                                toolHat.removeAttribute('role');
                                toolHat.removeAttribute('tabindex');
                                toolHat.removeAttribute('aria-expanded');
                                delete toolHat.dataset.boundToggle;
                            }
                            
                            toolHat.innerHTML = `
                                <div class="tool-hat-icon">
                                    <svg viewBox="0 0 20 20" width="14" height="14" fill="currentColor">
                                        <path d="${iconPath}"></path>
                                    </svg>
                                </div>
                                <div class="tool-hat-text">正在使用 ${toolName}...</div>
                            `;

                        } else if (data.type === 'tool_end') {
                            const toolName = data.name;
                            const idx = activeTools.indexOf(toolName);
                            if (idx !== -1) activeTools.splice(idx, 1);
                            suppressTokensUntilDone = activeTools.length > 0;
                            
                            // Smart Hat Management
                            const toolHat = contentDiv.querySelector('.tool-hat');
                            if (toolHat) {
                                if (activeTools.length > 0) {
                                    const nextName = activeTools[0];
                                    const textEl = toolHat.querySelector('.tool-hat-text');
                                    if (textEl) textEl.textContent = `正在使用 ${nextName}...`;
                                    const pathEl = toolHat.querySelector('.tool-hat-icon path');
                                    if (pathEl) pathEl.setAttribute('d', toolIconPaths[nextName] || TOOL_ICONS.default);
                                } else {
                                    lockToolHat(toolHat);
                                }
                            }
                        }

                    } catch (e) {
                        console.error('Error parsing JSON chunk:', e, 'Line:', line);
                        // 继续处理下一行，不中断整个流程
                    }
                }

                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }

            // Refetch calendar at the end of every message
            if (calendar) {
                calendar.refetchEvents();
            }

        } catch (err) {
            console.error('Request error:', err);

            // 重试逻辑：最多重试 5 次
            if (retryCount < 5) {
                const retryDelay = Math.min(1000 * Math.pow(2, retryCount), 5000); // 1s, 2s, 4s, 5s, 5s

                if (retryCount === 0) {
                    contentDiv.innerHTML = `<span class="error-message">⚠️ 请求失败，正在重试... (${retryCount + 1}/5)</span>`;
                } else {
                    contentDiv.innerHTML = `<span class="error-message">⚠️ 仍然失败，继续重试... (${retryCount + 1}/5)</span>`;
                }

                // 等待后重试
                await new Promise(resolve => setTimeout(resolve, retryDelay));
                return sendMessage(retryCount + 1, text);
            } else {
                // 5 次重试都失败，显示友好错误消息
                contentDiv.innerHTML = `
                    <div class="error-message">
                        <p>⚠️ <strong>技术问题，请稍后重试</strong></p>
                        <p style="font-size: 12px; opacity: 0.8;">AI 服务暂时无法响应，请检查网络连接或稍后再试。</p>
                        <button onclick="window.sendMessage(0, '${text.replace(/'/g, "\\'")}')" style="
                            margin-top: 10px;
                            padding: 6px 12px;
                            background: #ED0D92;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                            font-size: 12px;
                        ">重新发送</button>
                    </div>
                `;
            }
        }
    }

    function appendMessage(text, className) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${className}`;
        msgDiv.innerHTML = `<div class="message-content">${text}</div>`;
        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return msgDiv;
    }

    function showConfirmModal(options) {
        const modal = document.getElementById('confirmModal');
        const titleEl = document.getElementById('confirmTitle');
        const bodyEl = document.getElementById('confirmBody');
        const footerEl = document.getElementById('confirmFooter');
        const closeBtn = document.querySelector('.close-confirm-btn');

        if (!modal || !titleEl || !bodyEl || !footerEl || !closeBtn) {
            return Promise.resolve(window.confirm((options && options.message) || '确定吗？'));
        }

        const {
            title = '请确认',
            message = '',
            detail = '',
            confirmText = '确定',
            cancelText = '取消',
            danger = false
        } = options || {};

        titleEl.textContent = title;
        bodyEl.innerHTML = '';
        const msgP = document.createElement('div');
        msgP.style.fontWeight = '700';
        msgP.style.marginBottom = detail ? '10px' : '0';
        msgP.textContent = message;
        bodyEl.appendChild(msgP);
        if (detail) {
            const detailP = document.createElement('div');
            detailP.style.color = 'var(--text-secondary)';
            detailP.style.fontSize = '0.92rem';
            detailP.style.lineHeight = '1.5';
            detailP.textContent = detail;
            bodyEl.appendChild(detailP);
        }

        footerEl.innerHTML = '';
        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'secondary-btn';
        cancelBtn.type = 'button';
        cancelBtn.textContent = cancelText;
        const okBtn = document.createElement('button');
        okBtn.className = danger ? 'danger-btn' : 'primary-btn';
        okBtn.type = 'button';
        okBtn.textContent = confirmText;
        footerEl.appendChild(cancelBtn);
        footerEl.appendChild(okBtn);

        modal.style.display = 'flex';

        return new Promise((resolve) => {
            const cleanup = () => {
                cancelBtn.onclick = null;
                okBtn.onclick = null;
                closeBtn.onclick = null;
                modal.removeEventListener('click', onBackdropClick);
                document.removeEventListener('keydown', onKeyDown);
            };

            const close = (result) => {
                cleanup();
                modal.style.display = 'none';
                resolve(result);
            };

            const onBackdropClick = (e) => {
                if (e.target === modal) close(false);
            };

            const onKeyDown = (e) => {
                if (e.key === 'Escape') close(false);
            };

            cancelBtn.onclick = () => close(false);
            closeBtn.onclick = () => close(false);
            okBtn.onclick = () => close(true);

            modal.addEventListener('click', onBackdropClick);
            document.addEventListener('keydown', onKeyDown);
        });
    }

    // --- Manual Editing Logic ---
    const modal = document.getElementById('eventModal');
    const modalInfo = document.getElementById('modalInfo');
    const modalFooter = document.getElementById('modalFooter');
    let currentEventId = null;

    if (calendar) {
        calendar.setOption('eventClick', function (info) {
            currentEventId = info.event.id;
            showEditModal(info.event);
        });
    }

    document.querySelector('.close-modal-btn').onclick = () => {
        modal.style.display = "none";
    };

    if (modal) {
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    }

    function showEditModal(event) {
        const props = event.extendedProps;
        const start = event.startStr.slice(0, 16);
        const end = event.endStr.slice(0, 16);

        // 获取学生颜色
        const studentName = props.student_name || '';
        const colorInfo = getStudentColor(studentName);

        // 格式化时间显示
        const formatTime = (timeStr) => {
            const d = new Date(timeStr);
            return d.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        };

        // 生成详情视图HTML
        const detailHtml = `
        <div class="course-detail">
            <div class="detail-header" style="border-left-color: ${colorInfo.primary}">
                <div class="detail-title">${event.title || '未命名课程'}</div>
                ${studentName ? `<div class="detail-student" style="color: ${colorInfo.primary}">${studentName}</div>` : ''}
            </div>

            <div class="detail-list">
                <div class="detail-item" onclick="copyToClipboard('${event.title || ''}', '课程名称')">
                    <div class="detail-label">
                        <svg viewBox="0 0 20 20" width="16" height="16" fill="currentColor">
                            <path d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 0v12h8V4H6z"/>
                        </svg>
                        课程名称
                    </div>
                    <div class="detail-value copyable">${event.title || '-'}</div>
                </div>

                <div class="detail-item" onclick="copyToClipboard('${studentName}', '学生姓名')">
                    <div class="detail-label">
                        <svg viewBox="0 0 20 20" width="16" height="16" fill="currentColor">
                            <path d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"/>
                        </svg>
                        学生姓名
                    </div>
                    <div class="detail-value copyable" style="color: ${colorInfo.primary}">${studentName || '-'}</div>
                </div>

                <div class="detail-item" onclick="openLocationMap('${props.location || ''}')">
                    <div class="detail-label">
                        <svg viewBox="0 0 20 20" width="16" height="16" fill="currentColor">
                            <path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"/>
                        </svg>
                        上课地点
                    </div>
                    <div class="detail-value ${props.location ? 'linkable' : ''}">${props.location || '未设置'}</div>
                </div>

                <div class="detail-item" onclick="copyToClipboard('${formatTime(start)}', '开始时间')">
                    <div class="detail-label">
                        <svg viewBox="0 0 20 20" width="16" height="16" fill="currentColor">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"/>
                        </svg>
                        开始时间
                    </div>
                    <div class="detail-value copyable">${formatTime(start)}</div>
                </div>

                <div class="detail-item" onclick="copyToClipboard('${formatTime(end)}', '结束时间')">
                    <div class="detail-label">
                        <svg viewBox="0 0 20 20" width="16" height="16" fill="currentColor">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm.75-13a1.75 1.75 0 00-1.75 1.75v2.5a1.75 1.75 0 001.75 1.75h2.5a1.75 1.75 0 001.75-1.75v-2.5a1.75 1.75 0 00-1.75-1.75h-2.5z" clip-rule="evenodd"/>
                        </svg>
                        结束时间
                    </div>
                    <div class="detail-value copyable">${formatTime(end)}</div>
                </div>

                <div class="detail-item" onclick="copyToClipboard('${props.price || 0}', '价格')">
                    <div class="detail-label">
                        <svg viewBox="0 0 20 20" width="16" height="16" fill="currentColor">
                            <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z"/>
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clip-rule="evenodd"/>
                        </svg>
                        价格
                    </div>
                    <div class="detail-value copyable">${props.price || 0} 元</div>
                </div>
            </div>

            <div class="detail-actions">
                <button class="secondary-btn" onclick="enterEditMode()">编辑</button>
                <button class="danger-btn" onclick="deleteCourse('${event.id}')">删除</button>
            </div>
        </div>
        `;

        // 保存当前课程数据供编辑使用
        window.currentCourseData = {
            id: event.id,
            title: event.title,
            student_id: props.student_id,
            start: start,
            end: end,
            price: props.price,
            location: props.location || ''
        };

        modalInfo.innerHTML = detailHtml;
        modalFooter.innerHTML = `
            <button class="secondary-btn" onclick="closeModal()">关闭</button>
        `;
        modal.style.display = "flex";
    }

    // 复制到剪贴板
    window.copyToClipboard = function (text, label) {
        if (!text) {
            toastInfo('没有内容可复制');
            return;
        }
        navigator.clipboard.writeText(text).then(() => {
            toastSuccess(`已复制${label}: ${text}`);
        }).catch(() => {
            // 降级方案
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            toastSuccess(`已复制${label}: ${text}`);
        });
    };

    // 打开地点地图
    window.openLocationMap = function (location) {
        if (!location) {
            toastInfo('未设置上课地点');
            return;
        }
        // 跳转到高德地图搜索
        const mapUrl = `https://ditu.amap.com/search?query=${encodeURIComponent(location)}`;
        window.open(mapUrl, '_blank');
    };

    // 进入编辑模式
    window.enterEditMode = async function () {
        // Load students list before showing edit form
        await loadStudentsList();
        showModalContent(window.currentCourseData, false);
    };

    // 关闭弹窗
    window.closeModal = function () {
        modal.style.display = "none";
    };

    window.saveCourse = async function (id) {
        const title = document.getElementById('edit-title').value;
        const studentId = document.getElementById('edit-student').value;
        const start = document.getElementById('edit-start').value;
        const end = document.getElementById('edit-end').value;
        const price = parseFloat(document.getElementById('edit-price').value);
        const location = document.getElementById('edit-location').value;

        if (!title || !studentId || !start || !end) {
            toastError('请填写必要信息（课程名称和学生）');
            return;
        }

        try {
            const res = await fetch(`/api/courses/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: title,
                    student_id: parseInt(studentId),
                    start: start + ':00',
                    end: end + ':00',
                    price: price,
                    location: location
                })
            });

            if (res.ok) {
                toastSuccess('课程已更新');
                modal.style.display = 'none';
                calendar.refetchEvents();
            } else {
                const err = await res.json();
                toastError('保存失败: ' + (err.detail || '未知错误'));
            }
        } catch (e) {
            console.error(e);
            toastError('网络错误');
        }
    }

    window.deleteCourse = async function (id) {
        const ok = await showConfirmModal({
            title: '删除课程',
            message: '确定要删除这节课吗？',
            detail: '删除后无法恢复。',
            confirmText: '删除',
            cancelText: '取消',
            danger: true
        });
        if (!ok) return;

        try {
            const res = await fetch(`/api/courses/${id}`, { method: 'DELETE' });
            if (res.ok) {
                modal.style.display = 'none';
                calendar.refetchEvents();
                toastSuccess('已删除课程');
            } else {
                toastError('删除失败');
            }
        } catch (e) {
            console.error(e);
            toastError('网络错误');
        }
    }

    // --- UI Helpers ---
    function setModalTitle(title) {
        const titleEl = document.querySelector('.modal-header h2');
        if (titleEl) {
            titleEl.textContent = title;
        }
    }

    // --- Add Course Logic ---
    window.showAddModal = async function () {
        setModalTitle('添加新课程');
        // Load students list first
        await loadStudentsList();

        // Clear form or set defaults
        const now = new Date();
        const toLocalISO = (d) => {
            const offset = d.getTimezoneOffset() * 60000;
            return new Date(d.getTime() - offset).toISOString().slice(0, 16);
        };
        const nextHour = new Date();
        nextHour.setHours(nextHour.getHours() + 1);
        nextHour.setMinutes(0, 0, 0, 0);

        const endHour = new Date(nextHour);
        endHour.setHours(endHour.getHours() + 1);

        showModalContent({
            title: '',
            student_id: '',
            start: toLocalISO(nextHour),
            end: toLocalISO(endHour),
            price: 200, // Default price
            location: ''
        }, true); // true = isNew
    }

    function showModalContent(data, isNew = false) {
        if (!isNew) {
            setModalTitle('课程详情');
        }

        // Get student select HTML
        const studentSelectHtml = getStudentSelectHtml(data.student_id || '');

        const formHtml = `
        <div class="edit-form">
            <div class="form-group">
                <label>课程名称</label>
                <input type="text" id="edit-title" value="${data.title || ''}" placeholder="例如：钢琴课">
            </div>
            <div class="form-group">
                <label>学生</label>
                ${studentSelectHtml}
            </div>
            <div class="row-group">
                <div class="form-group">
                    <label>开始时间</label>
                    <input type="datetime-local" id="edit-start" value="${data.start}">
                </div>
                <div class="form-group">
                    <label>结束时间</label>
                    <input type="datetime-local" id="edit-end" value="${data.end}">
                </div>
            </div>
            <div class="row-group">
                 <div class="form-group">
                    <label>上课地点</label>
                    <input type="text" id="edit-location" value="${data.location || ''}" placeholder="例如：201教室">
                </div>
                <div class="form-group">
                    <label>价格 (元)</label>
                    <input type="number" id="edit-price" value="${data.price || 0}">
                </div>
            </div>
           
        </div>
    `;

        modalInfo.innerHTML = formHtml;

        let buttons = `
        <button class="secondary-btn" onclick="document.getElementById('eventModal').style.display='none'">取消</button>
    `;

        if (isNew) {
            buttons += `<button class="primary-btn" onclick="createCourse()">创建课程</button>`;
        } else {
            buttons = `
         <button class="danger-btn" onclick="deleteCourse('${data.id}')" style="margin-right:auto">删除</button>
         ` + buttons + `
         <button class="primary-btn" onclick="saveCourse('${data.id}')">保存修改</button>
         `;
        }

        modalFooter.innerHTML = buttons;
        modal.style.display = "flex";
    }

    window.createCourse = async function () {
        const title = document.getElementById('edit-title').value;
        const studentId = document.getElementById('edit-student').value;
        const start = document.getElementById('edit-start').value;
        const end = document.getElementById('edit-end').value;
        const price = parseFloat(document.getElementById('edit-price').value);
        const location = document.getElementById('edit-location').value;

        if (!title || !studentId || !start || !end) {
            toastError('请填写必要信息（课程名称和学生）');
            return;
        }

        try {
            const res = await fetch('/api/courses', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: title,
                    student_id: parseInt(studentId),
                    start: start + ':00',
                    end: end + ':00',
                    price: price,
                    location: location
                })
            });

            if (res.ok) {
                toastSuccess('课程创建成功');
                modal.style.display = 'none';
                calendar.refetchEvents();
            } else {
                const err = await res.json();
                toastError('创建失败: ' + (err.detail || '未知错误'));
            }
        } catch (e) {
            console.error(e);
            toastError('网络错误');
        }
    }

    // --- Tab Navigation ---
    window.switchTab = function (tabName) {
        const calendarView = document.getElementById('calendarView');
        const studentsView = document.getElementById('studentsView');
        const calendarBtn = document.querySelector('.tab-btn[data-tab="calendar"]');
        const studentsBtn = document.querySelector('.tab-btn[data-tab="students"]');
        const calendarAction = document.querySelector('.calendar-action');
        const studentAction = document.querySelector('.student-action');

        if (tabName === 'calendar') {
            calendarView.style.display = 'flex';
            studentsView.style.display = 'none';
            calendarBtn.classList.add('active');
            studentsBtn.classList.remove('active');
            calendarAction.style.display = 'flex';
            studentAction.style.display = 'none';
            // 刷新日历尺寸
            setTimeout(() => {
                if (calendar) {
                    calendar.updateSize();
                }
            }, 100);
        } else {
            calendarView.style.display = 'none';
            studentsView.style.display = 'flex';
            calendarBtn.classList.remove('active');
            studentsBtn.classList.add('active');
            calendarAction.style.display = 'none';
            studentAction.style.display = 'flex';
            // 加载学生列表
            loadStudents();
        }
    };

    // --- Student Management ---
    let studentsData = [];

    // Load students list for dropdown selection
    let allStudentsList = [];

    async function loadStudentsList() {
        try {
            const res = await fetch('/api/students');
            if (res.ok) {
                allStudentsList = await res.json();
                return allStudentsList;
            }
        } catch (e) {
            console.error('Failed to load students list:', e);
        }
        return [];
    }

    // Generate student select HTML
    function getStudentSelectHtml(selectedStudentId = '') {
        if (!allStudentsList || allStudentsList.length === 0) {
            return `
                <div class="no-students-hint">
                    <p>还没有学生信息</p>
                    <a href="#" onclick="switchTab('students'); closeModal(); return false;">去添加学生</a>
                </div>
            `;
        }

        const options = allStudentsList.map(s =>
            `<option value="${s.id}" ${s.id == selectedStudentId ? 'selected' : ''}>${s.name} ${s.grade ? '(' + s.grade + ')' : ''}</option>`
        ).join('');

        return `
            <select id="edit-student" class="student-select">
                <option value="" disabled ${!selectedStudentId ? 'selected' : ''}>请选择学生</option>
                ${options}
            </select>
        `;
    }

    window.loadStudents = async function () {
        const container = document.getElementById('studentsList');
        container.innerHTML = '<div class="empty-state"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg><p>加载中...</p></div>';

        try {
            const res = await fetch('/api/students');
            if (res.ok) {
                studentsData = await res.json();
                allStudentsList = studentsData; // Sync lists
                renderStudents();
            } else {
                container.innerHTML = '<div class="empty-state"><h3>加载失败</h3><p>请稍后重试</p></div>';
            }
        } catch (e) {
            console.error(e);
            // 如果API不存在，显示模拟数据
            renderMockStudents();
        }
    };

    function renderStudents() {
        const container = document.getElementById('studentsList');

        if (!studentsData || studentsData.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                        <circle cx="9" cy="7" r="4"/>
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                    </svg>
                    <h3>还没有学生</h3>
                    <p>点击右上角"添加学生"开始管理学生信息</p>
                </div>
            `;
            return;
        }

        container.innerHTML = studentsData.map(student => {
            const colorInfo = getStudentColor(student.name);
            const progress = student.progress || 0;

            return `
                <div class="student-card" style="--student-color: ${colorInfo.primary}">
                    <div class="student-header">
                        <div class="student-avatar">${student.name.charAt(0)}</div>
                        <div class="student-info">
                            <div class="student-name">${student.name}</div>
                            <div class="student-grade">
                                <svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor">
                                    <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 13A6 6 0 118 2a6 6 0 018 12z"/>
                                    <path d="M8 4a.5.5 0 01.5.5v3h3a.5.5 0 010 1h-3.5A.5.5 0 018 8V4.5a.5.5 0 01.5-.5z"/>
                                </svg>
                                ${student.grade || '未设置年级'}
                            </div>
                        </div>
                    </div>

                    <div class="student-details">
                        ${student.phone ? `
                            <div class="student-detail-item" onclick="copyToClipboard('${student.phone}', '电话')">
                                <div class="student-detail-icon">
                                    <svg viewBox="0 0 20 20" width="16" height="16" fill="currentColor">
                                        <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z"/>
                                    </svg>
                                </div>
                                <div class="student-detail-content">
                                    <div class="student-detail-label">联系电话</div>
                                    <div class="student-detail-value clickable">${student.phone}</div>
                                </div>
                            </div>
                        ` : ''}

                        ${student.parent_contact ? `
                            <div class="student-detail-item" onclick="copyToClipboard('${student.parent_contact}', '家长联系方式')">
                                <div class="student-detail-icon">
                                    <svg viewBox="0 0 20 20" width="16" height="16" fill="currentColor">
                                        <path d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 100 2 1 1 0 000-2zm1 5a1 1 0 10-2 0v3a1 1 0 102 0v-3z"/>
                                    </svg>
                                </div>
                                <div class="student-detail-content">
                                    <div class="student-detail-label">家长联系方式</div>
                                    <div class="student-detail-value clickable">${student.parent_contact}</div>
                                </div>
                            </div>
                        ` : ''}

                        ${student.notes ? `
                            <div class="student-detail-item">
                                <div class="student-detail-icon">
                                    <svg viewBox="0 0 20 20" width="16" height="16" fill="currentColor">
                                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                                    </svg>
                                </div>
                                <div class="student-detail-content">
                                    <div class="student-detail-label">备注</div>
                                    <div class="student-detail-value">${student.notes}</div>
                                </div>
                            </div>
                        ` : ''}
                    </div>

                    <div class="student-progress">
                        <div class="student-progress-label">
                            <span>学习进度</span>
                            <span>${progress}%</span>
                        </div>
                        <div class="student-progress-bar">
                            <div class="student-progress-fill" style="width: ${progress}%"></div>
                        </div>
                    </div>

                    <div class="student-actions">
                        <button class="edit-btn" onclick="editStudent('${student.id}')">编辑</button>
                        <button class="delete-btn" onclick="deleteStudent('${student.id}', '${student.name}')">删除</button>
                    </div>
                </div>
            `;
        }).join('');
    }

    function renderMockStudents() {
        const container = document.getElementById('studentsList');
        container.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
                <h3>还没有学生</h3>
                <p>点击右上角"添加学生"开始管理学生信息</p>
            </div>
        `;
    }

    window.showAddStudentModal = function () {
        setModalTitle('添加学生档案');
        const formHtml = `
        <div class="edit-form">
            <div class="form-group">
                <label>学生姓名 *</label>
                <input type="text" id="student-name" value="" placeholder="例如：小明">
            </div>
            <div class="form-group">
                <label>年级</label>
                <input type="text" id="student-grade" value="" placeholder="例如：小学三年级">
            </div>
            <div class="form-group">
                <label>联系电话</label>
                <input type="tel" id="student-phone" value="" placeholder="例如：13800138000">
            </div>
            <div class="form-group">
                <label>家长联系方式</label>
                <input type="text" id="student-parent" value="" placeholder="例如：小明妈妈 13900139000">
            </div>
            <div class="form-group">
                <label>学习进度 (%)</label>
                <input type="number" id="student-progress" value="0" min="0" max="100">
            </div>
            <div class="form-group">
                <label>备注</label>
                <textarea id="student-notes" rows="3" placeholder="学习特点、注意事项等..."></textarea>
            </div>
        </div>
        `;

        modalInfo.innerHTML = formHtml;
        modalFooter.innerHTML = `
            <button class="secondary-btn" onclick="closeModal()">取消</button>
            <button class="primary-btn" onclick="createStudent()">创建学生</button>
        `;
        modal.style.display = "flex";
    };

    window.createStudent = async function () {
        const name = document.getElementById('student-name').value.trim();
        const grade = document.getElementById('student-grade').value.trim();
        const phone = document.getElementById('student-phone').value.trim();
        const parent_contact = document.getElementById('student-parent').value.trim();
        const progress = parseInt(document.getElementById('student-progress').value) || 0;
        const notes = document.getElementById('student-notes').value.trim();

        if (!name) {
            toastError('请输入学生姓名');
            return;
        }

        try {
            const res = await fetch('/api/students', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name, grade, phone, parent_contact, progress, notes
                })
            });

            if (res.ok) {
                toastSuccess('学生添加成功');
                closeModal();
                loadStudents();
            } else {
                const err = await res.json();
                toastError('添加失败: ' + (err.detail || '未知错误'));
            }
        } catch (e) {
            console.error(e);
            toastError('网络错误');
        }
    };

    window.editStudent = async function (studentId) {
        setModalTitle('学生档案详情');
        const student = studentsData.find(s => s.id === parseInt(studentId) || s.id === studentId);
        if (!student) {
            toastError('学生信息不存在');
            return;
        }

        const formHtml = `
        <div class="edit-form">
            <input type="hidden" id="edit-student-id" value="${student.id}">
            <div class="form-group">
                <label>学生姓名 *</label>
                <input type="text" id="student-name" value="${student.name || ''}" placeholder="例如：小明">
            </div>
            <div class="form-group">
                <label>年级</label>
                <input type="text" id="student-grade" value="${student.grade || ''}" placeholder="例如：小学三年级">
            </div>
            <div class="form-group">
                <label>联系电话</label>
                <input type="tel" id="student-phone" value="${student.phone || ''}" placeholder="例如：13800138000">
            </div>
            <div class="form-group">
                <label>家长联系方式</label>
                <input type="text" id="student-parent" value="${student.parent_contact || ''}" placeholder="例如：小明妈妈 13900139000">
            </div>
            <div class="form-group">
                <label>学习进度 (%)</label>
                <input type="number" id="student-progress" value="${student.progress || 0}" min="0" max="100">
            </div>
            <div class="form-group">
                <label>备注</label>
                <textarea id="student-notes" rows="3" placeholder="学习特点、注意事项等...">${student.notes || ''}</textarea>
            </div>
        </div>
        `;

        modalInfo.innerHTML = formHtml;
        modalFooter.innerHTML = `
            <button class="secondary-btn" onclick="closeModal()">取消</button>
            <button class="primary-btn" onclick="updateStudent('${student.id}')">保存修改</button>
        `;
        modal.style.display = "flex";
    };

    window.updateStudent = async function (studentId) {
        const name = document.getElementById('student-name').value.trim();
        const grade = document.getElementById('student-grade').value.trim();
        const phone = document.getElementById('student-phone').value.trim();
        const parent_contact = document.getElementById('student-parent').value.trim();
        const progress = parseInt(document.getElementById('student-progress').value) || 0;
        const notes = document.getElementById('student-notes').value.trim();

        if (!name) {
            toastError('请输入学生姓名');
            return;
        }

        try {
            const res = await fetch(`/api/students/${studentId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name, grade, phone, parent_contact, progress, notes
                })
            });

            if (res.ok) {
                toastSuccess('学生信息已更新');
                closeModal();
                loadStudents();
                // 如果学生名字改了，刷新课程表以更新颜色
                calendar.refetchEvents();
            } else {
                const err = await res.json();
                toastError('更新失败: ' + (err.detail || '未知错误'));
            }
        } catch (e) {
            console.error(e);
            toastError('网络错误');
        }
    };

    window.deleteStudent = async function (studentId, studentName) {
        const ok = await showConfirmModal({
            title: '删除学生',
            message: `确定要删除学生“${studentName}”吗？`,
            detail: '删除后将同时删除该学生的所有课程记录，且无法恢复。',
            confirmText: '删除',
            cancelText: '取消',
            danger: true
        });
        if (!ok) return;

        try {
            const res = await fetch(`/api/students/${studentId}`, { method: 'DELETE' });

            if (res.ok) {
                toastSuccess(`学生"${studentName}"已删除`);
                closeModal();
                loadStudents();
                calendar.refetchEvents();
                // 清除该学生的颜色缓存
                if (studentColors[studentName]) {
                    delete studentColors[studentName];
                    localStorage.setItem('studentColors', JSON.stringify(studentColors));
                }
            } else {
                const err = await res.json();
                toastError('删除失败: ' + (err.detail || '未知错误'));
            }
        } catch (e) {
            console.error(e);
            toastError('网络错误');
        }
    };
});
