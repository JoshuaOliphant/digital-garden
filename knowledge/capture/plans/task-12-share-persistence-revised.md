ccc# Task 12: Share & State Persistence (REVISED)

## Overview
**Complexity**: 3/5 | **Dependencies**: Tasks 10, 11  
**Status**: Ready to implement

Since we removed Alpine.js in favor of pure JavaScript panel management, this task has been revised to focus on sharing functionality and enhanced state persistence for the Andy Matuschak-style sliding panel system.

## Context from Previous Tasks
- Task 10: Sliding Panel UI with pure JavaScript (panel-navigation.js)
- Task 11: Mobile Adaptation with responsive panels
- URL state management already functional via `updateURL()` and `initFromURL()`
- Panel state tracked in URL parameters: `?panels=notes/foo,til/bar&focus=1`

## Objectives
1. Implement native share API for mobile devices
2. Add clipboard copy fallback for desktop
3. Enable cross-tab synchronization
4. Add reading progress persistence
5. Implement panel state recovery after browser restart

## TDD Requirements - Write These Tests FIRST

### Share Functionality Tests
1. Test that share button appears on panel header
2. Test that clicking share on mobile triggers native share API
3. Test that share includes title and URL with panel state
4. Test that desktop fallback copies URL to clipboard
5. Test that share URL preserves exact panel configuration
6. Test that shared URLs open correctly in new sessions
7. Test that share button shows success feedback

### State Persistence Tests
8. Test that panel state saves to localStorage on changes
9. Test that localStorage state includes panel IDs and focus
10. Test that state restores on page refresh
11. Test that "Continue reading" prompt appears if state exists
12. Test that user can dismiss saved state
13. Test that localStorage cleans up old states (>30 days)

### Cross-Tab Synchronization Tests
14. Test that opening panels in one tab updates other tabs
15. Test that closing panels syncs across tabs
16. Test that focus changes propagate to other tabs
17. Test that storage events are properly handled
18. Test that sync respects user preference setting

### Progress Tracking Tests
19. Test that scroll position saves per panel
20. Test that reading time is tracked per panel
21. Test that progress indicators show completion percentage
22. Test that "Mark as read" functionality works
23. Test that reading history is maintained

### Performance Tests
24. Test that localStorage operations don't block UI
25. Test that state sync doesn't cause infinite loops
26. Test that share functionality responds within 100ms
27. Test that memory usage remains stable with persistence

## Implementation Approach

### 1. Share Functionality
```javascript
// Add to PanelManager class
async shareCurrentState() {
    const shareData = {
        title: `Garden Walk: ${this.panels.map(p => p.title).join(' → ')}`,
        text: `Reading path through ${this.panels.length} notes`,
        url: window.location.href
    };
    
    if (navigator.share && this.isMobile()) {
        try {
            await navigator.share(shareData);
            this.showNotification('Shared successfully!');
        } catch (err) {
            if (err.name !== 'AbortError') {
                this.fallbackShare(shareData.url);
            }
        }
    } else {
        this.fallbackShare(shareData.url);
    }
}

fallbackShare(url) {
    navigator.clipboard.writeText(url).then(() => {
        this.showNotification('Link copied to clipboard!');
    }).catch(() => {
        // Fallback to selection
        this.selectText(url);
        this.showNotification('Press Ctrl+C to copy');
    });
}
```

### 2. State Persistence
```javascript
// localStorage structure
const panelState = {
    version: 1,
    timestamp: Date.now(),
    panels: [
        {
            id: 'notes/garden-walk',
            scrollPosition: 250,
            readingTime: 120,
            completed: false
        }
    ],
    currentFocus: 0,
    totalReadingTime: 350
};

// Save state on changes
savePanelState() {
    const state = {
        version: 1,
        timestamp: Date.now(),
        panels: this.panels.map((p, i) => ({
            id: p.id,
            scrollPosition: this.getScrollPosition(i),
            readingTime: this.readingTimes[p.id] || 0,
            completed: this.completedPanels.has(p.id)
        })),
        currentFocus: this.currentPanel,
        url: window.location.href
    };
    
    localStorage.setItem('gardenWalkState', JSON.stringify(state));
}

// Restore on load
restorePanelState() {
    const saved = localStorage.getItem('gardenWalkState');
    if (!saved) return;
    
    const state = JSON.parse(saved);
    
    // Check if state is recent (< 7 days)
    const age = Date.now() - state.timestamp;
    if (age > 7 * 24 * 60 * 60 * 1000) {
        localStorage.removeItem('gardenWalkState');
        return;
    }
    
    // Offer to restore
    this.showRestorePrompt(state);
}
```

### 3. Cross-Tab Synchronization
```javascript
// Listen for storage events
window.addEventListener('storage', (e) => {
    if (e.key === 'gardenWalkSync' && e.newValue) {
        const sync = JSON.parse(e.newValue);
        if (sync.tabId !== this.tabId) {
            this.handleCrossTabSync(sync);
        }
    }
});

// Broadcast state changes
broadcastStateChange(action, data) {
    const sync = {
        tabId: this.tabId,
        timestamp: Date.now(),
        action: action, // 'open', 'close', 'focus'
        data: data
    };
    
    localStorage.setItem('gardenWalkSync', JSON.stringify(sync));
}
```

### 4. Reading Progress
```javascript
// Track reading progress
trackReadingProgress(panelIndex) {
    const panel = this.panels[panelIndex];
    const container = this.getPanelElement(panelIndex);
    const scrollContainer = container.querySelector('.panel-content');
    
    const progress = {
        scrollHeight: scrollContainer.scrollHeight,
        scrollTop: scrollContainer.scrollTop,
        clientHeight: scrollContainer.clientHeight,
        percentage: Math.round((scrollContainer.scrollTop + scrollContainer.clientHeight) / scrollContainer.scrollHeight * 100)
    };
    
    // Update reading time
    if (!this.readingTimes[panel.id]) {
        this.readingTimes[panel.id] = 0;
    }
    
    // Save progress
    this.panelProgress[panel.id] = progress;
    this.savePanelState();
    
    // Update progress indicator
    this.updateProgressIndicator(panelIndex, progress.percentage);
}
```

## UI Components

### Share Button
```html
<!-- Add to panel header -->
<button class="share-btn p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors" 
        title="Share reading path" 
        aria-label="Share current reading path">
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m9.032 4.026a3 3 0 10-2.684-2.684m0 0a3 3 0 00-2.684 2.684M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
</button>
```

### Continue Reading Prompt
```html
<!-- Restore state notification -->
<div class="restore-prompt fixed bottom-4 right-4 bg-white dark:bg-gray-800 shadow-lg rounded-lg p-4 max-w-sm">
    <p class="text-sm mb-3">Continue your garden walk from where you left off?</p>
    <div class="flex gap-2">
        <button class="restore-yes px-3 py-1 bg-emerald-500 text-white rounded text-sm">
            Continue (3 panels)
        </button>
        <button class="restore-no px-3 py-1 bg-gray-200 dark:bg-gray-700 rounded text-sm">
            Start Fresh
        </button>
    </div>
</div>
```

### Progress Indicator
```html
<!-- Add to panel -->
<div class="reading-progress absolute bottom-0 left-0 right-0 h-1 bg-gray-200 dark:bg-gray-700">
    <div class="progress-bar bg-emerald-500 h-full transition-all duration-300" 
         style="width: 0%"></div>
</div>
```

## Integration Steps

1. **Update panel-navigation.js**
   - Add share methods to PanelManager class
   - Implement localStorage persistence
   - Add cross-tab synchronization listeners
   - Create reading progress tracking

2. **Modify panel rendering**
   - Add share button to panel headers
   - Include progress indicators
   - Add "Mark as read" option

3. **Create restore UI**
   - Build restore prompt component
   - Add dismissal logic
   - Style for mobile and desktop

4. **Add utility functions**
   - Mobile detection helper
   - Clipboard fallback implementation
   - Storage cleanup routine

5. **Test across devices**
   - Verify native share on iOS/Android
   - Test clipboard on desktop browsers
   - Check cross-tab sync behavior

6. **Performance optimization**
   - Debounce localStorage writes
   - Throttle progress tracking
   - Limit stored history size

## Mobile Considerations

- Native share sheet on iOS/Android
- Touch-friendly share button (44px min)
- Reduced progress tracking frequency on mobile
- Simplified restore prompt for small screens

## Privacy & Settings

Consider adding user preferences:
```javascript
const userPreferences = {
    enableStateRestore: true,
    enableCrossTabSync: false,
    enableProgressTracking: true,
    autoCleanupDays: 30
};
```

## Success Criteria

- [ ] Share functionality works on all platforms
- [ ] State persists across browser sessions
- [ ] Cross-tab sync operates smoothly
- [ ] Reading progress tracked accurately
- [ ] No performance degradation
- [ ] Accessibility standards met
- [ ] Mobile experience optimized

## Notes

This revision focuses on practical enhancements that improve the user experience of the Andy Matuschak-style panel system. The share functionality makes it easy to send reading paths to others, while persistence ensures users never lose their place in their garden exploration.

The implementation should be additive - all existing panel functionality continues to work, with these features layered on top as progressive enhancements.