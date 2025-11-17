# Frontend Configuration Guide

This guide explains how to customize the TrustMed AI frontend without breaking anything.

## 📁 File Structure

```
frontend/
├── official_frontend_ollama.py         # Main frontend (CLEANED VERSION)
└── official_frontend_ollama_backup.py  # Backup of old version
```

---

## 🎨 Easy Customization (Design Tokens)

All visual settings are centralized at the **top of the CSS** in `official_frontend_ollama.py`. Look for the `:root` section (around line 45).

### Layout Dimensions

Edit these variables to change sizes:

```css
:root {
    /* ===== EDIT THESE TO CUSTOMIZE ===== */

    /* Width Controls */
    --main-container-max-width: 1600px;   /* Overall content area */
    --chat-area-max-width: 1400px;        /* Chat messages width */
    --input-box-max-width: 1400px;        /* Input field width */
    --welcome-max-width: 1400px;          /* Welcome screen width */
    --sidebar-width: 280px;               /* Sidebar width */

    /* Spacing */
    --sidebar-padding-top: 0.5rem;        /* Space above "AI Parameters" */
    --input-min-height: 38px;             /* Input field height */

    /* Colors */
    --bg-color: #fafafa;                  /* Background color */
    --text-primary: #333;                 /* Main text color */
    --input-bg: rgba(255, 255, 255, 0.95); /* Input background */
    --caret-color: #333;                  /* Text cursor color */
    --border-color: #e5e5e5;              /* Border color */

    /* ... more variables ... */
}
```

### Common Customizations

#### Make Chat Box Wider
```css
--input-box-max-width: 1600px;  /* Was 1400px */
--chat-area-max-width: 1600px;  /* Was 1400px */
```

#### Change Cursor Color
```css
--caret-color: #ff0000;  /* Red cursor */
```

#### Remove Sidebar Padding
```css
--sidebar-padding-top: 0;  /* No padding */
```

#### Make Input Taller
```css
--input-min-height: 50px;  /* Was 38px */
```

#### Change Theme Colors
```css
--bg-color: #ffffff;         /* White background */
--text-primary: #000000;     /* Black text */
--button-bg: #4CAF50;        /* Green button */
```

---

## 📐 CSS Organization

The CSS is organized into **clear sections** with headers:

```css
/* ========================================================================
   SECTION NAME - Description
   ======================================================================== */
```

### Sections:

1. **DESIGN TOKENS** - All customizable variables
2. **GLOBAL STYLES** - Font, background, Streamlit hiding
3. **MAIN CONTAINER** - Overall content width and layout
4. **SIDEBAR STYLING** - Sidebar appearance and spacing
5. **WELCOME SCREEN** - Initial screen styling
6. **CHAT INPUT BOX** - Bottom fixed input field
7. **CHAT AREA** - Message display area
8. **GRAPH INFO PANEL** - Knowledge graph source info
9. **PROCESSING STATUS** - Loading indicators
10. **LOADING SCREEN** - Initial page load animation
11. **RESPONSIVE DESIGN** - Mobile/tablet adjustments

### How to Find What You Need:

**Want to change input width?**
→ Search for `CHAT INPUT BOX` section

**Want to change sidebar spacing?**
→ Search for `SIDEBAR STYLING` section

**Want to change message bubbles?**
→ Search for `CHAT AREA` section

---

## 🔧 Common Issues and Fixes

### Issue 1: Width Changes Not Working

**Problem**: You changed `--input-box-max-width` but nothing happened

**Solution**:
1. Make sure you edited the `:root` section (top of CSS)
2. Clear Streamlit cache: `streamlit cache clear`
3. Hard refresh browser: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
4. Restart Streamlit completely

### Issue 2: Cursor Not Visible

**Problem**: Can't see the blinking cursor in input field

**Check these variables**:
```css
--caret-color: #333;              /* Dark cursor */
--input-bg: rgba(255, 255, 255, 0.95);  /* Light background */
```

Make sure cursor color contrasts with background!

### Issue 3: Sidebar Has Extra Space

**Problem**: Too much space above "AI Parameters"

**Solution**:
```css
--sidebar-padding-top: 0;  /* Reduce or set to 0 */
```

### Issue 4: Changes Not Applying

**Problem**: You made changes but they don't show up

**Streamlit caches CSS aggressively. Always do this:**

```bash
# Stop Streamlit (Ctrl+C)
streamlit cache clear
streamlit run frontend/official_frontend_ollama.py
```

Or in browser:
1. Press `F12` to open DevTools
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"

---

## 🎯 Quick Reference: Common Edits

### Make Everything Wider
```css
--main-container-max-width: 1800px;
--chat-area-max-width: 1600px;
--input-box-max-width: 1600px;
--welcome-max-width: 1600px;
```

### Dark Mode Colors
```css
--bg-color: #1a1a1a;
--text-primary: #ffffff;
--text-secondary: #cccccc;
--border-color: #333333;
--input-bg: rgba(40, 40, 40, 0.95);
```

### Larger Text
Find the font-size properties in each section:
```css
.welcome-title {
    font-size: 2.5rem;  /* Was 2rem */
}

.stTextInput input {
    font-size: 1.125rem !important;  /* Was 0.9375rem */
}
```

### Change App Name
Search for "TrustMed AI" in the file:
```python
page_title="Your App Name",  # Line ~26
```
```html
<div class="welcome-title">Welcome to Your App Name</div>  # Line ~714
```

---

## 🧪 Testing Your Changes

After making edits:

1. **Save the file**
2. **Clear cache**:
   ```bash
   streamlit cache clear
   ```
3. **Restart Streamlit**:
   ```bash
   streamlit run frontend/official_frontend_ollama.py
   ```
4. **Hard refresh browser**: `Ctrl+Shift+R`

---

## 🔄 Reverting Changes

If something breaks, restore from backup:

```bash
cd frontend
cp official_frontend_ollama_backup.py official_frontend_ollama.py
```

Or manually undo your changes using the section headers to find what you modified.

---

## 📝 Best Practices

### DO:
- ✅ Edit design tokens (`:root` variables) first
- ✅ Use section headers to find what you need
- ✅ Clear cache after every change
- ✅ Test on different screen sizes
- ✅ Keep a backup of working version

### DON'T:
- ❌ Edit multiple sections at once
- ❌ Remove section headers
- ❌ Forget to clear cache
- ❌ Mix inline styles with CSS variables
- ❌ Remove `!important` flags (Streamlit needs them)

---

## 🐛 Debugging

### Check if CSS is loading:
1. Open browser DevTools (`F12`)
2. Go to Elements tab
3. Look for `<style>` tag with your CSS
4. Verify your changes are present

### Check for CSS conflicts:
1. Open DevTools → Elements
2. Click on the input box element
3. Look at Styles panel on right
4. Check which rules are being applied
5. Look for crossed-out rules (overridden)

### Common Streamlit CSS selectors:
- `[data-testid="stSidebar"]` - Sidebar
- `[data-testid="stHorizontalBlock"]` - Row containers
- `[data-testid="column"]` - Column elements
- `.stTextInput` - Text input fields
- `.stButton` - Buttons

---

## 📊 Performance Tips

1. **Minimize CSS changes during development**
   - Edit → Save → Test one change at a time

2. **Use browser caching**
   - Once CSS is loaded, browser caches it
   - Only clear cache when testing changes

3. **Optimize for mobile**
   - Check responsive breakpoints (lines ~529-600)
   - Test on actual mobile devices

---

## 🆘 Getting Help

If you're stuck:

1. **Check this guide** for your specific issue
2. **Look at section headers** in the CSS to understand organization
3. **Use browser DevTools** to inspect what's actually rendering
4. **Restore from backup** if something breaks
5. **Start with design tokens** - don't edit complex CSS unless necessary

---

## 📚 Additional Resources

- **Streamlit Docs**: https://docs.streamlit.io/
- **CSS Variables Guide**: https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties
- **Flexbox Guide**: https://css-tricks.com/snippets/css/a-guide-to-flexbox/

---

**Last Updated**: 2025-01-16
**Clean Version Created**: frontend/official_frontend_ollama.py
**Backup Version**: frontend/official_frontend_ollama_backup.py
