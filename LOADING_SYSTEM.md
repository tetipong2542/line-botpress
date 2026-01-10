# Loading System - React Suspense Style 🎨

Pure CSS + JavaScript loading system inspired by React Suspense and Next.js.
**No external dependencies required!**

## 📦 Included Components

### 1. **Skeleton Loading** (Like React Suspense fallback)
- Card skeleton
- List skeleton
- Table skeleton
- Text skeleton
- Avatar skeleton

### 2. **Spinners**
- Simple spinner
- Dots spinner
- Pulse spinner

### 3. **Page Transitions**
- Top loading bar (YouTube/Next.js style)
- Page overlay
- Fade in/out animations

### 4. **Button Loading States**
- Automatic disable on loading
- Built-in spinner
- Preserve original text

### 5. **API Call Indicators**
- Section loading
- Inline loading
- Empty state loading

---

## 🚀 Quick Start

### Basic Usage

#### 1. Show Skeleton While Loading Data (React Suspense Pattern)

```html
<!-- HTML: Initial skeleton -->
<div id="products-list" class="skeleton-list">
    <div class="skeleton-list-item">
        <div class="skeleton skeleton-avatar"></div>
        <div style="flex: 1;">
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-text-sm"></div>
        </div>
    </div>
</div>

<script>
// JavaScript: Load data and replace skeleton
async function loadProducts() {
    const container = document.getElementById('products-list');

    try {
        const products = await API.get('/products');

        // Replace skeleton with real data
        container.innerHTML = products.map(product => `
            <div class="product-item">
                <img src="${product.image}" />
                <h3>${product.name}</h3>
                <p>${product.price}</p>
            </div>
        `).join('');

        // Add fade-in animation
        container.classList.add('fade-in');
    } catch (error) {
        container.innerHTML = '<p>Error loading products</p>';
    }
}

document.addEventListener('DOMContentLoaded', loadProducts);
</script>
```

#### 2. Button Loading State

```html
<button id="save-btn" class="btn-primary" onclick="handleSave()">
    <span>Save</span>
</button>

<script>
async function handleSave() {
    const btn = document.getElementById('save-btn');

    // Wrap async operation with loading state
    await LoadingManager.withLoading(
        async () => {
            await API.post('/save', data);
            showToast('Saved successfully!', 'success');
        },
        { button: btn }
    );
}
</script>
```

#### 3. Page Loading Overlay

```javascript
// Show loading overlay
LoadingManager.showPageLoading('กำลังบันทึก...');

try {
    await API.post('/endpoint', data);
} finally {
    LoadingManager.hidePageLoading();
}
```

#### 4. Top Loading Bar (Next.js style)

```javascript
// Start loading bar
LoadingManager.startTopBar();

// After data loaded
LoadingManager.finishTopBar();
```

---

## 🎯 Advanced Examples

### Example 1: Complete Page Load Pattern

```javascript
async function loadPage() {
    const container = document.getElementById('content');

    // Method 1: Using withLoading helper
    await LoadingManager.withLoading(
        async () => {
            const data = await API.get('/data');
            renderData(data);
        },
        {
            element: container,
            skeletonType: 'list',  // card, list, table, text
            topBar: true
        }
    );
}
```

### Example 2: Form Submission with Multiple Loading States

```javascript
async function handleSubmit(e) {
    e.preventDefault();

    const submitBtn = e.target.querySelector('button[type="submit"]');
    const formContainer = document.getElementById('form-container');

    await LoadingManager.withLoading(
        async () => {
            // Your async operation
            await API.post('/submit', formData);
            showToast('Success!', 'success');
        },
        {
            button: submitBtn,      // Disable button + show spinner
            topBar: true,           // Show top loading bar
            // overlay: true        // Optional: full page overlay
        }
    );
}
```

### Example 3: Automatic Page Transitions

Page transitions are automatic! Just navigate normally:

```html
<!-- Will automatically show loading bar -->
<a href="/dashboard">Go to Dashboard</a>

<!-- Skip transition for specific links -->
<a href="/page" data-no-transition>No Transition</a>
```

---

## 📋 CSS Classes Reference

### Skeleton Components

| Class | Description |
|-------|-------------|
| `.skeleton` | Base skeleton with shimmer animation |
| `.skeleton-text` | Text line skeleton (16px height) |
| `.skeleton-text-sm` | Small text (12px height) |
| `.skeleton-text-lg` | Large text (20px height) |
| `.skeleton-circle` | Circular skeleton |
| `.skeleton-avatar` | Avatar (40x40px circle) |
| `.skeleton-avatar-lg` | Large avatar (60x60px circle) |
| `.skeleton-card` | Pre-made card skeleton |
| `.skeleton-list` | Pre-made list skeleton |
| `.skeleton-list-item` | List item skeleton |
| `.skeleton-table-row` | Table row skeleton |

### Spinners

| Class | Description |
|-------|-------------|
| `.spinner` | Default spinner (24px) |
| `.spinner-sm` | Small spinner (16px) |
| `.spinner-lg` | Large spinner (32px) |
| `.spinner-dots` | Three dots bouncing |
| `.spinner-pulse` | Pulsing circle |

### Loading States

| Class | Description |
|-------|-------------|
| `.btn-loading` | Button with hidden spinner |
| `.page-loading` | Initially hidden page |
| `.page-loaded` | Page with fade-in animation |
| `.fade-in` | Fade in animation |
| `.fade-out` | Fade out animation |
| `.loading-blur` | Blur content while loading |

---

## 🎨 Customization

### Change Primary Color

```css
:root {
    --primary-color: #your-color;
}
```

All spinners and loading bars will use your primary color automatically!

### Custom Skeleton Colors

```css
.skeleton {
    background: linear-gradient(
        90deg,
        #your-start 0%,
        #your-middle 50%,
        #your-end 100%
    );
}
```

---

## 🌙 Dark Mode

All components automatically support dark mode through CSS variables:

```css
@media (prefers-color-scheme: dark) {
    /* Automatically handled */
}
```

---

## 📱 Responsive Design

All components are mobile-friendly and adjust automatically on small screens.

---

## ⚡ Performance Tips

1. **Preload skeleton** - Show skeleton immediately in HTML
2. **Remove skeleton** - Remove skeleton elements after data loads (don't just hide)
3. **Use topBar for fast loads** - For quick operations (<500ms), use top loading bar instead of skeleton
4. **Lazy load sections** - Load different sections independently with their own skeletons

---

## 🔧 API Reference

### LoadingManager

| Method | Parameters | Description |
|--------|------------|-------------|
| `showPageLoading(message)` | message: string | Show full page overlay |
| `hidePageLoading()` | - | Hide page overlay |
| `startTopBar()` | - | Start top loading bar |
| `finishTopBar()` | - | Finish top loading bar |
| `setButtonLoading(button, loading)` | button: HTMLElement, loading: boolean | Toggle button loading state |
| `showSkeleton(element, type)` | element: HTMLElement, type: string | Show skeleton in element |
| `hideSkeleton(element)` | element: HTMLElement | Hide skeleton |
| `withLoading(fn, options)` | fn: async function, options: object | Wrap async function with loading states |

### withLoading Options

```javascript
{
    button: HTMLElement,      // Button to show loading state
    overlay: boolean,         // Show page overlay
    topBar: boolean,          // Show top loading bar
    element: HTMLElement,     // Element to show skeleton
    skeletonType: string      // 'card', 'list', 'table', 'text'
}
```

---

## 📝 Migration Guide

### From Old Loading to New System

**Before:**
```javascript
button.disabled = true;
button.innerHTML = 'Loading...';
```

**After:**
```javascript
LoadingManager.setButtonLoading(button, true);
```

**Before:**
```html
<div class="empty-state">
    <p>Loading...</p>
</div>
```

**After:**
```html
<div class="skeleton-list">
    <div class="skeleton-list-item">...</div>
    <div class="skeleton-list-item">...</div>
</div>
```

---

## 🎯 Best Practices

1. ✅ **Use skeletons for perceived performance** - Users feel page loads faster
2. ✅ **Match skeleton to actual content** - Same layout as real data
3. ✅ **Remove skeleton DOM after load** - Don't just hide it
4. ✅ **Use withLoading helper** - Automatic cleanup and error handling
5. ✅ **Show loading for >300ms operations** - Skip for instant operations
6. ❌ **Don't use multiple loading indicators** - Choose one: skeleton OR spinner OR overlay

---

## 🐛 Troubleshooting

**Skeleton not showing?**
- Check if `loading.css` is loaded
- Verify element has correct class names

**Button stays disabled?**
- Make sure to call `setButtonLoading(button, false)` in finally block
- Or use `withLoading` helper for automatic cleanup

**Top bar not disappearing?**
- Always call `finishTopBar()` after `startTopBar()`
- Use in try-finally to ensure cleanup

---

## 📚 Examples in Project

See these files for real examples:
- `/templates/categories.html` - Skeleton list loading
- `/templates/budgets.html` - Card skeleton loading
- (More will be added as we implement)

---

Built with ❤️ - No dependencies, just pure CSS + vanilla JS!
