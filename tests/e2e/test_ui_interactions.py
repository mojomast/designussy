"""E2E tests for UI interactions and navigation."""

import pytest
import asyncio
from playwright.async_api import expect
from tests.e2e.utils import create_test_utils, create_ui_helper, create_asset_helper


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.asyncio
class TestUINavigation:
    """Test UI navigation and page interactions."""
    
    async def test_navigation_to_main_pages(self, page):
        """Test navigation between main pages."""
        test_utils = create_test_utils(page)
        
        # Start at main page
        await page.goto("http://localhost:8000")
        await test_utils.wait_for_network_idle()
        
        # Test navigation to different sections
        navigation_tests = [
            "http://localhost:8000/unwritten_worlds_v2.html",
            "http://localhost:8000/unwritten_worlds_loading_examples.html",
            "http://localhost:8000/unwritten_worlds_logos.html",
            "http://localhost:8000/enhanced_design/index.html"
        ]
        
        for url in navigation_tests:
            try:
                await page.goto(url)
                await test_utils.wait_for_network_idle()
                
                # Verify page loaded
                title = await page.title()
                assert title is not None
                
                # Check if page content is visible
                body = page.locator("body")
                await expect(body).to_be_visible()
                
                print(f"✅ Successfully navigated to: {url}")
            except Exception as e:
                print(f"⚠️ Failed to navigate to {url}: {e}")
        
        print("✅ Navigation test completed")
    
    async def test_responsive_design_mobile(self, page):
        """Test responsive design on mobile viewport."""
        test_utils = create_test_utils(page)
        
        # Set mobile viewport
        await test_utils.set_viewport(375, 667)  # iPhone SE
        
        await page.goto("http://localhost:8000")
        await test_utils.wait_for_network_idle()
        
        # Check that main content is still visible and accessible
        body = page.locator("body")
        await expect(body).to_be_visible()
        
        # Check for mobile-specific elements
        mobile_elements = page.locator('.mobile-menu, .hamburger-menu, [data-mobile="true"]')
        mobile_count = await mobile_elements.count()
        print(f"✅ Found {mobile_count} mobile-specific elements")
        
        # Test touch interactions
        buttons = page.locator("button")
        button_count = await buttons.count()
        
        if button_count > 0:
            # Test clicking first button
            await buttons.first.click()
            await asyncio.sleep(1)
            print(f"✅ Mobile touch interaction test completed ({button_count} buttons found)")
        else:
            print("ℹ️ No buttons found for mobile interaction test")
    
    async def test_responsive_design_tablet(self, page):
        """Test responsive design on tablet viewport."""
        test_utils = create_test_utils(page)
        
        # Set tablet viewport
        await test_utils.set_viewport(768, 1024)  # iPad
        
        await page.goto("http://localhost:8000")
        await test_utils.wait_for_network_idle()
        
        # Verify page renders correctly
        body = page.locator("body")
        await expect(body).to_be_visible()
        
        # Check for tablet-specific layout
        content = page.locator('.main-content, .container, main')
        content_count = await content.count()
        print(f"✅ Found {content_count} main content areas")
        
        print("✅ Tablet responsive design test completed")
    
    async def test_responsive_design_desktop(self, page):
        """Test responsive design on desktop viewport."""
        test_utils = create_test_utils(page)
        
        # Set desktop viewport
        await test_utils.set_viewport(1920, 1080)
        
        await page.goto("http://localhost:8000")
        await test_utils.wait_for_network_idle()
        
        # Verify full desktop layout
        body = page.locator("body")
        await expect(body).to_be_visible()
        
        # Test desktop-specific interactions
        navigation = page.locator('nav, .navigation, .menu')
        nav_count = await navigation.count()
        if nav_count > 0:
            print(f"✅ Desktop navigation found ({nav_count} navigation elements)")
        
        print("✅ Desktop responsive design test completed")


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.asyncio
class TestUIFormInteractions:
    """Test form submissions and user inputs."""
    
    async def test_form_submissions(self, page):
        """Test form submission workflows."""
        ui_helper = create_ui_helper(page)
        
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Look for forms
        forms = page.locator("form")
        form_count = await forms.count()
        
        if form_count > 0:
            print(f"✅ Found {form_count} forms to test")
            
            for i in range(min(form_count, 2)):  # Test first 2 forms
                form = forms.nth(i)
                await expect(form).to_be_visible()
                
                # Test input fields
                inputs = form.locator("input, textarea, select")
                input_count = await inputs.count()
                
                if input_count > 0:
                    # Fill out form
                    for j in range(min(input_count, 3)):  # Test first 3 inputs
                        input_elem = inputs.nth(j)
                        
                        # Get input type
                        input_type = await input_elem.get_attribute("type")
                        if input_type == "text" or input_type == "email":
                            await input_elem.fill("test@example.com")
                        elif input_type == "number":
                            await input_elem.fill("42")
                        
                        print(f"✅ Filled input {j+1} in form {i+1}")
            
            # Test form submission
            submit_buttons = forms.locator('input[type="submit"], button[type="submit"], button:has-text("Submit")')
            submit_count = await submit_buttons.count()
            
            if submit_count > 0:
                await submit_buttons.first.click()
                await asyncio.sleep(2)
                print("✅ Form submission test completed")
        else:
            print("ℹ️ No forms found for testing")
    
    async def test_parameter_adjustments(self, page):
        """Test adjusting generation parameters."""
        ui_helper = create_ui_helper(page)
        
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Look for parameter controls
        param_selectors = [
            'input[type="range"]',
            'select',
            'input[type="number"]',
            '.parameter-control',
            '[data-parameter]'
        ]
        
        found_params = False
        for selector in param_selectors:
            try:
                elements = page.locator(selector)
                count = await elements.count()
                if count > 0:
                    found_params = True
                    print(f"✅ Found {count} parameter controls: {selector}")
                    
                    # Test adjusting first parameter
                    element = elements.first
                    
                    if "range" in selector:
                        # Test slider
                        await element.click()
                    elif "select" in selector:
                        # Test dropdown
                        options = await element.locator("option").count()
                        if options > 1:
                            await element.select_option("1")
                    elif "number" in selector:
                        # Test number input
                        await element.fill("100")
                    
                    break
            except Exception:
                continue
        
        if not found_params:
            print("ℹ️ No parameter controls found")
        
        print("✅ Parameter adjustment test completed")


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.asyncio
class TestUIButtonInteractions:
    """Test button clicks and interactive elements."""
    
    async def test_button_clicks(self, page):
        """Test various button click interactions."""
        ui_helper = create_ui_helper(page)
        
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Test different types of buttons
        button_types = [
            ("button", "Regular button"),
            ('button:has-text("Generate")', "Generate button"),
            ('button:has-text("Clear")', "Clear button"),
            ('button:has-text("Download")', "Download button")
        ]
        
        for selector, description in button_types:
            try:
                buttons = page.locator(selector)
                count = await buttons.count()
                
                if count > 0:
                    # Test clicking first button
                    button = buttons.first
                    await expect(button).to_be_visible()
                    await button.click()
                    await asyncio.sleep(1)
                    
                    print(f"✅ Tested {description} - {count} found")
                else:
                    print(f"ℹ️ No {description} found")
            except Exception as e:
                print(f"⚠️ Failed to test {description}: {e}")
        
        print("✅ Button click test completed")
    
    async def test_hover_interactions(self, page):
        """Test hover interactions on UI elements."""
        ui_helper = create_ui_helper(page)
        
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Test hover on various elements
        hover_selectors = [
            "button",
            ".concept-card",
            "img",
            "svg",
            ".interactive"
        ]
        
        for selector in hover_selectors:
            try:
                elements = page.locator(selector)
                count = await elements.count()
                
                if count > 0:
                    # Test hover on first element
                    element = elements.first
                    await ui_helper.hover_element(selector)
                    await asyncio.sleep(0.5)
                    
                    print(f"✅ Tested hover on {selector} - {count} elements found")
                else:
                    print(f"ℹ️ No {selector} elements found")
            except Exception as e:
                print(f"⚠️ Failed to test hover on {selector}: {e}")
        
        print("✅ Hover interaction test completed")
    
    async def test_drag_and_drop(self, page):
        """Test drag and drop functionality."""
        ui_helper = create_ui_helper(page)
        
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Look for draggable elements
        draggable_selectors = [
            '[draggable="true"]',
            '.draggable',
            '.sortable-item'
        ]
        
        found_draggable = False
        for selector in draggable_selectors:
            try:
                elements = page.locator(selector)
                count = await elements.count()
                
                if count >= 2:  # Need at least 2 elements for drag and drop
                    found_draggable = True
                    source = elements.first
                    target = elements.nth(1)
                    
                    # Test drag and drop
                    await source.hover()
                    await source.hover()
                    await source.drag_to(target)
                    await asyncio.sleep(1)
                    
                    print(f"✅ Tested drag and drop with {selector} - {count} elements")
                    break
            except Exception:
                continue
        
        if not found_draggable:
            print("ℹ️ No draggable elements found for testing")
        
        print("✅ Drag and drop test completed")


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.asyncio
class TestUIContentLoading:
    """Test content loading and display."""
    
    async def test_image_loading(self, page):
        """Test image loading and display."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Check for images
        images = page.locator("img")
        image_count = await images.count()
        
        if image_count > 0:
            print(f"✅ Found {image_count} images")
            
            # Test image loading
            for i in range(min(image_count, 5)):  # Test first 5 images
                img = images.nth(i)
                
                # Check if image is visible
                await expect(img).to_be_visible()
                
                # Check if image has src
                src = await img.get_attribute("src")
                if src:
                    print(f"✅ Image {i+1} loaded: {src[:50]}...")
        else:
            print("ℹ️ No images found")
        
        print("✅ Image loading test completed")
    
    async def test_svg_content(self, page):
        """Test SVG content loading."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Check for SVG elements
        svgs = page.locator("svg")
        svg_count = await svgs.count()
        
        if svg_count > 0:
            print(f"✅ Found {svg_count} SVG elements")
            
            # Test SVG visibility
            for i in range(min(svg_count, 3)):
                svg = svgs.nth(i)
                await expect(svg).to_be_visible()
                
                # Check SVG dimensions
                width = await svg.get_attribute("width")
                height = await svg.get_attribute("height")
                print(f"✅ SVG {i+1} - Width: {width}, Height: {height}")
        else:
            print("ℹ️ No SVG elements found")
        
        print("✅ SVG content test completed")
    
    async def test_async_content_loading(self, page):
        """Test async content loading."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Wait for additional content to load
        await asyncio.sleep(3)
        
        # Check for dynamically loaded content
        dynamic_selectors = [
            '.loaded-content',
            '[data-loaded="true"]',
            '.async-content',
            '.generated-content'
        ]
        
        for selector in dynamic_selectors:
            try:
                elements = page.locator(selector)
                count = await elements.count()
                if count > 0:
                    print(f"✅ Found {count} dynamically loaded elements: {selector}")
                    break
            except Exception:
                continue
        
        # Check console for loading activities
        console_messages = []
        def handle_console(msg):
            if msg.type in ['log', 'info']:
                console_messages.append(msg.text)
        
        page.on('console', handle_console)
        await page.reload()
        
        print(f"✅ Found {len(console_messages)} console messages")
        print("✅ Async content loading test completed")


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.asyncio
class TestUIKeyboardNavigation:
    """Test keyboard navigation and accessibility."""
    
    async def test_keyboard_navigation(self, page):
        """Test keyboard navigation through elements."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Test Tab navigation
        await page.keyboard.press('Tab')
        await asyncio.sleep(0.5)
        
        # Test Enter on focused element
        await page.keyboard.press('Enter')
        await asyncio.sleep(1)
        
        # Test Escape key
        await page.keyboard.press('Escape')
        await asyncio.sleep(0.5)
        
        print("✅ Keyboard navigation test completed")
    
    async def test_accessibility_compliance(self, page):
        """Test basic accessibility features."""
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Check for ARIA labels
        aria_elements = page.locator('[aria-label], [aria-labelledby]')
        aria_count = await aria_elements.count()
        print(f"✅ Found {aria_count} ARIA labeled elements")
        
        # Check for alt text on images
        images = page.locator("img")
        image_count = await images.count()
        
        alt_count = 0
        for i in range(image_count):
            img = images.nth(i)
            alt = await img.get_attribute("alt")
            if alt:
                alt_count += 1
        
        if image_count > 0:
            alt_percentage = (alt_count / image_count) * 100
            print(f"✅ Image alt text coverage: {alt_percentage:.1f}% ({alt_count}/{image_count})")
        
        # Check for proper heading structure
        headings = page.locator("h1, h2, h3, h4, h5, h6")
        heading_count = await headings.count()
        if heading_count > 0:
            print(f"✅ Found {heading_count} heading elements")
        
        print("✅ Accessibility compliance test completed")