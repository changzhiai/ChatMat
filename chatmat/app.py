import streamlit as st
import streamlit.components.v1 as components
import requests
import py3Dmol
import re
from stmol import showmol

# --- Configuration ---
# ⚠️ This must match the address where your FastAPI backend is running
BACKEND_URL = "http://127.0.0.1:8000/calculate/"

st.set_page_config(page_title="ChatMat", layout="wide", page_icon="⚛️")

# --- Custom CSS for Chat Styling ---
st.markdown("""
<style>
    .chat-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .user-msg {
        text-align: right;
        color: #0f52ba;
        font-weight: bold;
    }
    .bot-msg {
        text-align: left;
        color: #333;
    }
    /* Prevent body scroll interference */
    #root > div > div {
        overflow: visible !important;
    }
    
    /* Layout structure for columns */
    div[data-testid="column"] {
        display: flex !important;
        flex-direction: column !important;
    }
    
    /* Left column: Chat interface with sticky form at bottom */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child {
        position: relative !important;
        height: calc(100vh - 2rem) !important;
        max-height: calc(100vh - 2rem) !important;
        display: flex !important;
        flex-direction: column !important;
    }
    
    /* Make the vertical block in left column a flex container */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child > div[data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
        max-height: 100% !important;
        min-height: 0 !important;
    }
    
    /* Chat history wrapper - scrollable */
    .chat-history-wrapper {
        flex: 1 1 auto !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        padding-right: 10px !important;
        margin-bottom: 10px !important;
        min-height: 0 !important;
        max-height: 100% !important;
        height: 0 !important; /* Force flex item to respect parent height */
        -webkit-overflow-scrolling: touch !important; /* Smooth scrolling on mobile */
    }
    
    /* Custom scrollbar styling for chat history */
    .chat-history-wrapper::-webkit-scrollbar {
        width: 8px;
    }
    
    .chat-history-wrapper::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    .chat-history-wrapper::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 4px;
    }
    
    .chat-history-wrapper::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    
    /* Chat form - sticky at bottom */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child form[data-testid="stForm"],
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child .stForm {
        position: sticky !important;
        bottom: 0 !important;
        z-index: 100 !important;
        background-color: #ffffff !important;
        margin-top: auto !important;
        flex-shrink: 0 !important;
    }
    
    /* Right column: Sticky visualizer */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {
        position: sticky !important;
        top: 20px !important;
        align-self: flex-start !important;
        max-height: calc(100vh - 40px) !important;
        overflow-y: auto !important;
    }
    /* Hide the submit button */
    form[data-testid="stForm"] button[type="submit"],
    button[data-testid="stBaseButton-secondaryFormSubmit"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        opacity: 0 !important;
    }
    /* Add grey frame around form with smaller bottom margin */
    form[data-testid="stForm"],
    .stForm {
        border: 1px solid #d3d3d3 !important;
        border-radius: 5px !important;
        padding: 5px 5px 5px 5px !important;
        background-color: #ffffff !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        margin-bottom: 5px !important;
        gap: 0 !important;
    }
    /* Remove gap from form children */
    form[data-testid="stForm"] > *,
    .stForm > * {
        gap: 0 !important;
        margin: 0 !important;
    }
    /* Reduce gap between form rows to 0 */
    form[data-testid="stForm"] > div {
        margin-bottom: 0 !important;
        gap: 0 !important;
    }
    form[data-testid="stForm"] div[data-testid="stVerticalBlock"] {
        margin-bottom: 0 !important;
        margin-top: 0 !important;
    }

    /* Specifically target the dropdown container */
    form[data-testid="stForm"] div[data-testid="stVerticalBlock"].st-emotion-cache-wfksaw,
    form[data-testid="stForm"] div[data-testid="stVerticalBlock"][class*="e196pkbe2"] {
        padding: 0 !important;
        margin: 0 !important;
        gap: 0 !important;
        height: auto !important;
        min-height: 0 !important;
    }

    form[data-testid="stForm"] div[data-baseweb="select"] > div,
    form[data-testid="stForm"] div[data-baseweb="select"] button,
    form[data-testid="stForm"] div[data-baseweb="select"] > div > div,
    form[data-testid="stForm"] div[data-baseweb="select"] button > div {
        background-color: #f0f2f6 !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        font-size: 0.85rem !important;
    }

    /* Target nested divs and buttons in selectbox */
    form[data-testid="stForm"] div[data-baseweb="select"] > div,
    form[data-testid="stForm"] div[data-baseweb="select"] > div > div,
    form[data-testid="stForm"] div[data-testid="stSelectbox"] > div {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    /* Clamp the form row and columns to 30px */
    form[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {
        padding: 0 !important;
        margin: 0 !important;
        height: 30px !important;
        min-height: 30px !important;
        max-height: 30px !important;
        display: flex !important;
        align-items: flex-start !important;
    }
    form[data-testid="stForm"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        padding: 0 !important;
        margin: 0 !important;
        height: 30px !important;
        min-height: 30px !important;
        max-height: 30px !important;
        display: flex !important;
        align-items: flex-start !important;
    }
    /* Compact Agent column/container */
    form[data-testid="stForm"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child {
        height: 30px !important;
        min-height: 30px !important;
        padding: 0 !important;
        margin: 0 !important;
        display: flex !important;
        align-items: flex-start !important;
        justify-content: flex-start !important;
    }
    form[data-testid="stForm"] div[data-testid="stElementContainer"] {
        height: 30px !important;
        min-height: 30px !important;
        max-height: 30px !important;
        line-height: 30px !important;
        padding: 0 !important;
        margin: 0 !important;
        display: flex !important;
        align-items: flex-start !important;
        justify-content: flex-start !important;
        overflow: hidden !important;
    }
    form[data-testid="stForm"] div[data-testid="stElementContainer"] iframe {
        height: 30px !important;
        min-height: 30px !important;
        max-height: 30px !important;
        margin: 0 !important;
        padding: 0 !important;
        display: block !important;
        vertical-align: top !important;
        overflow: hidden !important;
    }
    #agentSelect {
        height: 30px !important;
        min-height: 30px !important;
        line-height: 30px !important;
        padding: 0 6px !important;
        margin: 0 !important;
        font-size: 0.9rem !important;
        box-sizing: border-box !important;
        display: block !important;
    }
    /* Compact Agent column/container */
    form[data-testid="stForm"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child {
        height: 30px !important;
        min-height: 30px !important;
        align-items: flex-start !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    form[data-testid="stForm"] div[data-testid="stElementContainer"] {
        height: 30px !important;
        min-height: 30px !important;
        max-height: 30px !important;
        padding: 0 !important;
        margin: 0 !important;
        display: flex !important;
        align-items: flex-start !important;
        overflow: hidden !important;
    }
    /* Custom Agent select sizing */
    #agentSelect {
        height: 30px !important;
        min-height: 30px !important;
        line-height: 30px !important;
        padding: 0 6px !important;
        margin: 0 !important;
        font-size: 0.9rem !important;
        box-sizing: border-box !important;
        display: block !important;
    }
    /* Remove red outline from selectbox (Agent) on focus */
    div[data-baseweb="select"]:focus,
    div[data-baseweb="select"]:focus-within,
    div[data-baseweb="select"]:focus-visible,
    div[data-testid="stSelectbox"]:focus,
    div[data-testid="stSelectbox"]:focus-within,
    div[data-testid="stSelectbox"]:focus-visible {
        outline: none !important;
        outline-width: 0 !important;
        outline-style: none !important;
        outline-color: #f0f2f6 !important;
        box-shadow: none !important;
        border-color: #f0f2f6 !important;
        background-color: #f0f2f6 !important;
    }
    div[data-baseweb="select"] button:focus,
    div[data-baseweb="select"] button:focus-visible,
    div[data-baseweb="select"] > div:focus,
    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-visible {
        outline: none !important;
        outline-color: #f0f2f6 !important;
        box-shadow: none !important;
        border-color: #f0f2f6 !important;
        background-color: #f0f2f6 !important;
    }
    /* Set default border and background for selectbox */
    div[data-baseweb="select"],
    div[data-baseweb="select"] button,
    div[data-baseweb="select"] > div {
        border-color: #d3d3d3 !important;
        background-color: #f0f2f6 !important;
        border-radius: 4px !important;
        font-size: 0.85rem !important;
    }
    /* Target all text elements inside selectbox */
    div[data-baseweb="select"] *,
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div,
    div[data-testid="stSelectbox"] *,
    div[data-testid="stSelectbox"] span,
    div[data-testid="stSelectbox"] div {
        font-size: 0.85rem !important;
    }
    /* Target dropdown menu (popover) and options */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] *,
    ul[role="listbox"],
    ul[role="listbox"] *,
    li[role="option"],
    li[role="option"] *,
    div[data-baseweb="menu"],
    div[data-baseweb="menu"] * {
        font-size: 0.85rem !important;
    }
    /* Make dropdown open upward - JavaScript will handle positioning */
    div[data-baseweb="popover"] {
        bottom: auto !important;
    }
    /* Hide the underlying Agent combobox input (keep dropdown visible) */
    input[role="combobox"][aria-label*="Agent"],
    input[aria-label*="Selected Agent"],
    div[data-baseweb="select"] input[role="combobox"],
    div[data-testid="stSelectbox"] input[role="combobox"] {
        position: absolute !important;
        left: -9999px !important;
        width: 1px !important;
        height: 1px !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
    /* Ensure button and all nested elements have grey background by default */
    div[data-baseweb="select"] button,
    div[data-baseweb="select"] button > div,
    div[data-baseweb="select"] button > div > div,
    div[data-baseweb="select"] > div > button,
    div[data-baseweb="select"] > div > div > button,
    div[data-testid="stSelectbox"] button,
    div[data-testid="stSelectbox"] button > div,
    div[data-testid="stSelectbox"] > div > button {
        background-color: #f0f2f6 !important;
        border-radius: 4px !important;
        font-size: 0.85rem !important;
        padding: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
    /* On focus, make border match background */
    div[data-baseweb="select"]:focus,
    div[data-baseweb="select"]:focus-within,
    div[data-baseweb="select"]:focus-visible,
    div[data-baseweb="select"] button:focus,
    div[data-baseweb="select"] button:focus-visible {
        border-color: #f0f2f6 !important;
        outline-color: #f0f2f6 !important;
        background-color: #f0f2f6 !important;
    }
    /* Remove outline on input focus */
    input:focus,
    input:focus-visible,
    input:focus-within,
    input[data-testid="stTextInput"]:focus,
    input[type="text"]:focus,
    textarea:focus,
    textarea:focus-visible {
        outline: none !important;
        outline-width: 0 !important;
        outline-style: none !important;
        border-color: #ffffff !important;
        box-shadow: none !important;
    }
    /* Remove outline from Streamlit input containers and BaseWeb components */
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextInput"] input:focus-visible,
    div[data-baseweb="input"] input:focus,
    div[data-baseweb="input"] input:focus-visible,
    div[data-baseweb="input"]:focus,
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="input"]:focus-visible {
        outline: none !important;
        outline-width: 0 !important;
        outline-style: none !important;
        box-shadow: none !important;
        border-color: #ffffff !important;
    }
    /* Target BaseWeb input wrapper */
    div[data-baseweb="input"] > div:focus,
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="input"] > div:focus-visible,
    div[data-baseweb="input"] > div > input:focus {
        outline: none !important;
        outline-width: 0 !important;
        outline-style: none !important;
        box-shadow: none !important;
        border-color: #ffffff !important;
    }
    /* Set default border color, background, and remove outline for input elements */
    input,
    input[type="text"],
    div[data-testid="stTextInput"] input,
    div[data-baseweb="input"] input {
        border: none !important;
        border-color: transparent !important;
        background-color: #ffffff !important;
        outline: none !important;
        outline-width: 0 !important;
        outline-style: none !important;
        box-shadow: none !important;
    }
    /* Set background color and remove outline/border for input containers */
    div[data-baseweb="input"],
    div[data-baseweb="input"] > div,
    div[data-baseweb="input"] > div > div,
    div[data-testid="stTextInput"] {
        background-color: #ffffff !important;
        border: none !important;
        border-color: transparent !important;
        outline: none !important;
        outline-width: 0 !important;
        outline-style: none !important;
        box-shadow: none !important;
    }
    /* On focus, make border match background and remove outline */
    input:focus,
    input:focus-visible,
    div[data-testid="stTextInput"] input:focus,
    div[data-baseweb="input"] input:focus,
    div[data-baseweb="input"] input:focus-visible {
        border-color: #ffffff !important;
        outline: none !important;
        outline-width: 0 !important;
        outline-style: none !important;
    }
    /* Remove border and outline from error states and validation */
    input[aria-invalid="true"],
    div[data-baseweb="input"][aria-invalid="true"] input,
    div[data-baseweb="input"] input[aria-invalid="true"],
    div[data-baseweb="input"].st-ae input,
    div[data-baseweb="input"]:has(input[aria-invalid="true"]) {
        border-color: #ffffff !important;
        outline: none !important;
        outline-width: 0 !important;
        outline-style: none !important;
        box-shadow: none !important;
    }
    div[data-baseweb="input"]:focus,
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="input"]:focus-visible {
        border-color: #ffffff !important;
        outline: none !important;
        outline-width: 0 !important;
        outline-style: none !important;
        box-shadow: none !important;
    }
    /* Target any nested divs that might have borders - remove by default */
    div[data-baseweb="input"] > div,
    div[data-baseweb="input"] > div > div {
        border: none !important;
        border-color: transparent !important;
        outline: none !important;
        outline-width: 0 !important;
        outline-style: none !important;
        box-shadow: none !important;
    }
    div[data-baseweb="input"]:focus > div,
    div[data-baseweb="input"]:focus-within > div,
    div[data-baseweb="input"]:focus > div > div,
    div[data-baseweb="input"]:focus-within > div > div {
        border-color: #ffffff !important;
        outline: none !important;
        outline-width: 0 !important;
        outline-style: none !important;
    }
</style>
<script>
    // Function to set font size for dropdown menu
    function setDropdownFontSize() {
        const dropdownMenus = document.querySelectorAll('div[data-baseweb="popover"], ul[role="listbox"], div[data-baseweb="menu"]');
        dropdownMenus.forEach(menu => {
            menu.style.fontSize = '0.85rem';
            const allMenuElements = menu.querySelectorAll('*');
            allMenuElements.forEach(el => {
                el.style.fontSize = '0.85rem';
            });
        });
    }
    
    // Function to position dropdown upward
    function positionDropdownUpward() {
        // Use MutationObserver to catch when popover appears and position it upward
        const observer = new MutationObserver(() => {
            const popover = document.querySelector('div[data-baseweb="popover"]');
            if (popover && popover.style.display !== 'none' && popover.offsetParent !== null) {
                // Find the selectbox that's currently open
                const allSelectboxes = document.querySelectorAll('div[data-baseweb="select"], div[data-testid="stSelectbox"]');
                allSelectboxes.forEach(selectbox => {
                    const button = selectbox.querySelector('button');
                    if (button && button.getAttribute('aria-expanded') === 'true') {
                        const selectboxRect = selectbox.getBoundingClientRect();
                        const popoverRect = popover.getBoundingClientRect();
                        // Position popover above the selectbox
                        const topPosition = selectboxRect.top - popoverRect.height - 4;
                        popover.style.top = topPosition + 'px';
                        popover.style.bottom = 'auto';
                        popover.style.transform = 'none';
                        popover.style.position = 'fixed';
                    }
                });
            }
        });
        observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['style', 'aria-expanded'] });
        
        // Also listen for click events on selectbox buttons
        document.addEventListener('click', function(e) {
            const button = e.target.closest('div[data-baseweb="select"] button, div[data-testid="stSelectbox"] button');
            if (button) {
                setTimeout(() => {
                    const popover = document.querySelector('div[data-baseweb="popover"]');
                    if (popover) {
                        const selectbox = button.closest('div[data-baseweb="select"], div[data-testid="stSelectbox"]');
                        if (selectbox) {
                            const selectboxRect = selectbox.getBoundingClientRect();
                            const popoverRect = popover.getBoundingClientRect();
                            // Position popover above the selectbox
                            const topPosition = selectboxRect.top - popoverRect.height - 4;
                            popover.style.top = topPosition + 'px';
                            popover.style.bottom = 'auto';
                            popover.style.transform = 'none';
                            popover.style.position = 'fixed';
                        }
                    }
                }, 50);
            }
        }, true);
    }
    
    function removeRedOutline() {
        const bgColor = '#ffffff'; // Match background color
        
        // Remove outline and border from all inputs by default
        const inputs = document.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            // Set background color to white and remove border/outline by default
            input.style.backgroundColor = bgColor;
            input.style.border = 'none';
            input.style.borderColor = 'transparent';
            input.style.outline = 'none';
            input.style.outlineWidth = '0';
            input.style.outlineStyle = 'none';
            input.style.boxShadow = 'none';
            
            input.addEventListener('focus', function(e) {
                e.target.style.outline = 'none';
                e.target.style.outlineWidth = '0';
                e.target.style.outlineStyle = 'none';
                e.target.style.outlineColor = bgColor;
                e.target.style.boxShadow = 'none';
                e.target.style.border = 'none';
                e.target.style.borderColor = 'transparent';
                e.target.style.backgroundColor = bgColor;
            }, true);
            
            input.addEventListener('focusin', function(e) {
                e.target.style.outline = 'none';
                e.target.style.outlineColor = bgColor;
                e.target.style.boxShadow = 'none';
                e.target.style.border = 'none';
                e.target.style.borderColor = 'transparent';
                e.target.style.backgroundColor = bgColor;
            }, true);
        });
        
        // Also target parent containers that might have borders
        const inputContainers = document.querySelectorAll('div[data-baseweb="input"], div[data-testid="stTextInput"]');
        inputContainers.forEach(container => {
            // Set background color to white and remove borders/outlines by default
            container.style.backgroundColor = bgColor;
            container.style.border = 'none';
            container.style.borderColor = 'transparent';
            container.style.outline = 'none';
            container.style.outlineWidth = '0';
            container.style.outlineStyle = 'none';
            container.style.boxShadow = 'none';
            
            // Set background and remove borders for nested divs
            const nestedDivs = container.querySelectorAll('div');
            nestedDivs.forEach(div => {
                div.style.backgroundColor = bgColor;
                div.style.border = 'none';
                div.style.borderColor = 'transparent';
                div.style.outline = 'none';
                div.style.outlineWidth = '0';
                div.style.outlineStyle = 'none';
                div.style.boxShadow = 'none';
            });
            
            container.addEventListener('focusin', function(e) {
                const input = container.querySelector('input');
                if (input) {
                    input.style.outline = 'none';
                    input.style.outlineColor = bgColor;
                    input.style.boxShadow = 'none';
                    input.style.border = 'none';
                    input.style.borderColor = 'transparent';
                    input.style.backgroundColor = bgColor;
                }
                container.style.outline = 'none';
                container.style.outlineColor = bgColor;
                container.style.boxShadow = 'none';
                container.style.border = 'none';
                container.style.borderColor = 'transparent';
                container.style.backgroundColor = bgColor;
                
                // Also target nested divs
                const nestedDivs = container.querySelectorAll('div');
                nestedDivs.forEach(div => {
                    div.style.border = 'none';
                    div.style.borderColor = 'transparent';
                    div.style.outline = 'none';
                    div.style.outlineColor = bgColor;
                    div.style.backgroundColor = bgColor;
                });
            }, true);
        });
        
        // Set background color for selectbox (Agent dropdown)
        const selectBgColor = '#f0f2f6'; // Light grey background for selectbox
        const selectColor = '#f0f2f6'; // Light grey for borders/outlines
        const selectContainers = document.querySelectorAll('div[data-baseweb="select"], div[data-testid="stSelectbox"]');
        selectContainers.forEach(container => {
            // Set background color, border radius, and font size immediately
            container.style.backgroundColor = selectBgColor;
            container.style.borderRadius = '4px';
            container.style.fontSize = '0.85rem';
            container.style.padding = '0';
            container.style.paddingTop = '0';
            container.style.paddingBottom = '0';
            container.style.paddingLeft = '0';
            container.style.paddingRight = '0';
            
            // Set background and font size for all nested elements (more aggressive)
            const allElements = container.querySelectorAll('*');
            allElements.forEach(el => {
                el.style.fontSize = '0.85rem';
                if (el.tagName === 'BUTTON' || el.tagName === 'DIV' || el.tagName === 'SPAN') {
                    el.style.backgroundColor = selectBgColor;
                    el.style.padding = '0';
                    el.style.paddingTop = '0';
                    el.style.paddingBottom = '0';
                    el.style.paddingLeft = '0';
                    el.style.paddingRight = '0';
                    if (el.tagName === 'BUTTON') {
                        el.style.borderRadius = '4px';
                    }
                }
            });
            
            // Specifically target the button element
            const button = container.querySelector('button');
            if (button) {
                button.style.backgroundColor = selectBgColor;
                button.style.borderRadius = '4px';
                button.style.fontSize = '0.85rem';
                button.style.paddingTop = '0';
                button.style.paddingBottom = '0';
                button.style.marginTop = '0';
                button.style.marginBottom = '0';
                // Set background and font size for all children of button
                const buttonChildren = button.querySelectorAll('*');
                buttonChildren.forEach(child => {
                    child.style.backgroundColor = selectBgColor;
                    child.style.fontSize = '0.85rem';
                    child.style.paddingTop = '0';
                    child.style.paddingBottom = '0';
                });
                
                // When button is clicked, set font size for dropdown menu
                button.addEventListener('click', function() {
                    setTimeout(setDropdownFontSize, 50);
                }, true);
            }
            
            container.addEventListener('focusin', function(e) {
                container.style.outline = 'none';
                container.style.outlineColor = selectColor;
                container.style.boxShadow = 'none';
                container.style.borderColor = selectColor;
                container.style.backgroundColor = selectBgColor;
                
                // Target button and nested divs
                const button = container.querySelector('button');
                if (button) {
                    button.style.outline = 'none';
                    button.style.outlineColor = selectColor;
                    button.style.boxShadow = 'none';
                    button.style.borderColor = selectColor;
                    button.style.backgroundColor = selectBgColor;
                }
                
                const nestedDivs = container.querySelectorAll('div');
                nestedDivs.forEach(div => {
                    div.style.borderColor = selectColor;
                    div.style.outline = 'none';
                    div.style.outlineColor = selectColor;
                    div.style.backgroundColor = selectBgColor;
                });
            }, true);
            
            // Also handle button focus directly
            const button = container.querySelector('button');
            if (button) {
                button.style.backgroundColor = selectBgColor;
                button.addEventListener('focus', function(e) {
                    e.target.style.outline = 'none';
                    e.target.style.outlineColor = selectColor;
                    e.target.style.boxShadow = 'none';
                    e.target.style.borderColor = selectColor;
                    e.target.style.backgroundColor = selectBgColor;
                }, true);
            }
        });
        
        // Also set background for the column containing the selectbox
        const form = document.querySelector('form[data-testid="stForm"]');
        if (form) {
            const horizontalBlock = form.querySelector('div[data-testid="stHorizontalBlock"]');
            if (horizontalBlock) {
                const firstColumn = horizontalBlock.querySelector('div[data-testid="column"]:first-child');
                if (firstColumn) {
                    firstColumn.style.backgroundColor = selectBgColor;
                    firstColumn.style.borderRadius = '4px';
                    firstColumn.style.padding = '0';
                    firstColumn.style.paddingTop = '0';
                    firstColumn.style.paddingBottom = '0';
                }
            }
        }
    }
    
    // Function to apply selectbox background color
    function applySelectboxBackground() {
        const selectBgColor = '#f0f2f6';
        const selectContainers = document.querySelectorAll('div[data-baseweb="select"], div[data-testid="stSelectbox"]');
        selectContainers.forEach(container => {
            container.style.backgroundColor = selectBgColor;
            container.style.borderRadius = '4px';
            container.style.fontSize = '0.85rem';
            container.style.padding = '0';
            container.style.paddingTop = '0';
            container.style.paddingBottom = '0';
            container.style.paddingLeft = '0';
            container.style.paddingRight = '0';
            const allElements = container.querySelectorAll('*');
            allElements.forEach(el => {
                el.style.fontSize = '0.85rem';
                if (el.tagName === 'BUTTON' || el.tagName === 'DIV' || el.tagName === 'SPAN') {
                    el.style.backgroundColor = selectBgColor;
                    if (el.tagName === 'BUTTON') {
                        el.style.borderRadius = '4px';
                        el.style.padding = '0';
                        el.style.paddingTop = '0';
                        el.style.paddingBottom = '0';
                        el.style.paddingLeft = '0';
                        el.style.paddingRight = '0';
                        el.style.marginTop = '0';
                        el.style.marginBottom = '0';
                    }
                }
            });
            
            // Specifically target the button element
            const button = container.querySelector('button');
            if (button) {
                button.style.backgroundColor = selectBgColor;
                button.style.borderRadius = '4px';
                button.style.fontSize = '0.85rem';
                button.style.padding = '0';
                button.style.paddingTop = '0';
                button.style.paddingBottom = '0';
                button.style.paddingLeft = '0';
                button.style.paddingRight = '0';
                button.style.marginTop = '0';
                button.style.marginBottom = '0';
                // Set background and font size for all children of button
                const buttonChildren = button.querySelectorAll('*');
                buttonChildren.forEach(child => {
                    child.style.backgroundColor = selectBgColor;
                    child.style.fontSize = '0.85rem';
                    child.style.padding = '0';
                    child.style.paddingTop = '0';
                    child.style.paddingBottom = '0';
                    child.style.paddingLeft = '0';
                    child.style.paddingRight = '0';
                });
            }
        });
        
        // Also set background for the column containing the selectbox
        const form = document.querySelector('form[data-testid="stForm"]');
        if (form) {
            const horizontalBlock = form.querySelector('div[data-testid="stHorizontalBlock"]');
            if (horizontalBlock) {
                const firstColumn = horizontalBlock.querySelector('div[data-testid="column"]:first-child');
                if (firstColumn) {
                    firstColumn.style.backgroundColor = selectBgColor;
                    firstColumn.style.borderRadius = '4px';
                    firstColumn.style.padding = '0';
                    firstColumn.style.paddingTop = '0';
                    firstColumn.style.paddingBottom = '0';
                    firstColumn.style.paddingLeft = '0';
                    firstColumn.style.paddingRight = '0';
                }
            }
        }
    }
    
    // Apply immediately when script runs
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            removeRedOutline();
            applySelectboxBackground();
            positionDropdownUpward();
        });
    } else {
        removeRedOutline();
        applySelectboxBackground();
        positionDropdownUpward();
    }
    
    // Function to apply sticky layouts
    function applyStickyLayouts() {
        // Find the main horizontal block with columns
        const horizontalBlock = document.querySelector('div[data-testid="stHorizontalBlock"]');
        if (!horizontalBlock) return;
        
        const columns = horizontalBlock.querySelectorAll('div[data-testid="column"]');
        if (columns.length < 2) return;
        
        // Left column: Chat interface
        const leftColumn = columns[0];
        leftColumn.style.position = 'relative';
        leftColumn.style.height = 'calc(100vh - 2rem)';
        leftColumn.style.maxHeight = 'calc(100vh - 2rem)';
        leftColumn.style.display = 'flex';
        leftColumn.style.flexDirection = 'column';
        
        // Find the vertical block in left column
        const leftVerticalBlock = leftColumn.querySelector('div[data-testid="stVerticalBlock"]');
        if (leftVerticalBlock) {
            leftVerticalBlock.style.display = 'flex';
            leftVerticalBlock.style.flexDirection = 'column';
            leftVerticalBlock.style.height = '100%';
            leftVerticalBlock.style.maxHeight = '100%';
            leftVerticalBlock.style.minHeight = '0';
        }
        
        // Find and ensure chat history wrapper exists and is styled
        let chatHistoryWrapper = leftColumn.querySelector('.chat-history-wrapper');
        const form = leftColumn.querySelector('form[data-testid="stForm"]');
        
        // If wrapper doesn't exist, try to create it by finding chat messages
        if (!chatHistoryWrapper && form) {
            // Find the vertical block that should contain everything
            if (leftVerticalBlock) {
                // Find all elements before the form
                const allChildren = Array.from(leftVerticalBlock.children);
                const formIndex = allChildren.findIndex(el => el.contains(form) || el === form);
                
                if (formIndex > 0) {
                    // Create wrapper
                    chatHistoryWrapper = document.createElement('div');
                    chatHistoryWrapper.className = 'chat-history-wrapper';
                    
                    // Move elements before form into wrapper (including title)
                    const elementsToWrap = allChildren.slice(0, formIndex);
                    elementsToWrap.forEach(el => {
                        if (!el.classList.contains('chat-history-wrapper')) {
                            chatHistoryWrapper.appendChild(el);
                        }
                    });
                    
                    // Insert wrapper before form
                    if (formIndex < allChildren.length) {
                        leftVerticalBlock.insertBefore(chatHistoryWrapper, allChildren[formIndex]);
                    } else {
                        leftVerticalBlock.appendChild(chatHistoryWrapper);
                    }
                }
            } else {
                // Fallback: try to find chat messages and wrap them
                const chatMessages = leftColumn.querySelectorAll('.chat-container');
                if (chatMessages.length > 0) {
                    const firstMessage = chatMessages[0];
                    let commonParent = firstMessage.parentElement;
                    
                    // Find parent that contains form
                    while (commonParent && !commonParent.contains(form) && commonParent !== leftColumn) {
                        commonParent = commonParent.parentElement;
                    }
                    
                    if (commonParent && commonParent !== leftColumn) {
                        const allChildren = Array.from(commonParent.children);
                        const formIndex = allChildren.findIndex(el => el.contains(form) || el === form);
                        
                        if (formIndex > 0) {
                            chatHistoryWrapper = document.createElement('div');
                            chatHistoryWrapper.className = 'chat-history-wrapper';
                            
                            const elementsToWrap = allChildren.slice(0, formIndex);
                            elementsToWrap.forEach(el => {
                                if (!el.classList.contains('chat-history-wrapper')) {
                                    chatHistoryWrapper.appendChild(el);
                                }
                            });
                            
                            if (formIndex < allChildren.length) {
                                commonParent.insertBefore(chatHistoryWrapper, allChildren[formIndex]);
                            } else {
                                commonParent.appendChild(chatHistoryWrapper);
                            }
                        }
                    }
                }
            }
        }
        
        if (chatHistoryWrapper) {
            // Ensure wrapper has correct styles for scrolling
            chatHistoryWrapper.style.flex = '1 1 auto';
            chatHistoryWrapper.style.overflowY = 'auto';
            chatHistoryWrapper.style.overflowX = 'hidden';
            chatHistoryWrapper.style.paddingRight = '10px';
            chatHistoryWrapper.style.marginBottom = '10px';
            chatHistoryWrapper.style.minHeight = '0';
            chatHistoryWrapper.style.maxHeight = '100%';
            chatHistoryWrapper.style.height = '0'; // Force flex item to respect parent height
            chatHistoryWrapper.style.webkitOverflowScrolling = 'touch'; // Smooth scrolling
            
            // Function to recalculate height
            const recalculateHeight = () => {
                const form = leftColumn.querySelector('form[data-testid="stForm"]');
                if (form && leftVerticalBlock) {
                    // Use requestAnimationFrame to ensure DOM is updated
                    requestAnimationFrame(() => {
                        const formHeight = form.offsetHeight || form.getBoundingClientRect().height;
                        const parentHeight = leftVerticalBlock.offsetHeight || leftVerticalBlock.getBoundingClientRect().height;
                        const availableHeight = parentHeight - formHeight - 30; // 30px for margins and padding
                        if (availableHeight > 0) {
                            chatHistoryWrapper.style.maxHeight = availableHeight + 'px';
                        }
                    });
                }
            };
            
            // Recalculate immediately and after a delay
            recalculateHeight();
            setTimeout(recalculateHeight, 100);
            setTimeout(recalculateHeight, 500);
            
            // Handle window resize
            window.addEventListener('resize', recalculateHeight);
        }
        
        // Make form sticky at bottom
        if (form) {
            form.style.position = 'sticky';
            form.style.bottom = '0';
            form.style.zIndex = '100';
            form.style.backgroundColor = '#ffffff';
            form.style.marginTop = 'auto';
            form.style.flexShrink = '0';
        }
        
        // Right column: Sticky visualizer
        const rightColumn = columns[1];
        rightColumn.style.position = 'sticky';
        rightColumn.style.top = '20px';
        rightColumn.style.alignSelf = 'flex-start';
        rightColumn.style.maxHeight = 'calc(100vh - 40px)';
        rightColumn.style.overflowY = 'auto';
    }
    
    window.addEventListener('load', () => {
        // Apply sticky layouts
        applyStickyLayouts();
        
        // Find the right column (second column in the horizontal block)
        const horizontalBlock = document.querySelector('div[data-testid="stHorizontalBlock"]');
        if (horizontalBlock) {
            const columns = horizontalBlock.querySelectorAll('div[data-testid="column"]');
            if (columns.length >= 2) {
                const rightColumn = columns[1];
                rightColumn.style.position = 'sticky';
                rightColumn.style.top = '20px';
                rightColumn.style.alignSelf = 'flex-start';
                rightColumn.style.maxHeight = 'calc(100vh - 40px)';
                rightColumn.style.overflowY = 'auto';
            }
        }
        
        // Remove red outline
        removeRedOutline();
        
        // Apply background color immediately
        applySelectboxBackground();
        
        // Position dropdown upward
        positionDropdownUpward();
        
        // Set dropdown font size
        setDropdownFontSize();
        
        // Use requestAnimationFrame to apply after Streamlit renders
        requestAnimationFrame(() => {
            applyStickyLayouts();
            applySelectboxBackground();
            positionDropdownUpward();
            setDropdownFontSize();
        });
        
        // Also run after a short delay to catch dynamically loaded inputs
        setTimeout(() => {
            applyStickyLayouts();
            removeRedOutline();
            applySelectboxBackground();
            positionDropdownUpward();
            setDropdownFontSize();
        }, 100);
        
        setTimeout(() => {
            applyStickyLayouts();
            applySelectboxBackground();
            positionDropdownUpward();
            setDropdownFontSize();
        }, 500);
        
        // Use MutationObserver to catch inputs added dynamically and dropdown menus
        const observer = new MutationObserver(() => {
            applyStickyLayouts();
            removeRedOutline();
            applySelectboxBackground();
            positionDropdownUpward();
            // Set font size for dropdown menus when they appear
            setDropdownFontSize();
        });
        observer.observe(document.body, { childList: true, subtree: true, attributes: true });
        
        // Also observe the main app container for Streamlit reruns
        const appContainer = document.querySelector('#root');
        if (appContainer) {
            const appObserver = new MutationObserver(() => {
                setTimeout(() => {
                    applyStickyLayouts();
                }, 50);
            });
            appObserver.observe(appContainer, { childList: true, subtree: true });
        }
    });
</script>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "history" not in st.session_state:
    st.session_state.history = []
if "last_structure_xyz" not in st.session_state:
    st.session_state.last_structure_xyz = None

# --- Sidebar: Instructions ---
with st.sidebar:
    st.header("⚛️ ChatMat Control")
    st.write("This tool uses a foundation model to calculate energy and forces for material structures.")
    
    # Debug Mode Toggle
    debug_mode = st.checkbox("🐛 Debug Mode", value=False, help="Show detailed debugging information")
    st.markdown("### Try these prompts:")
    st.code("Calculate energy for a 2x2x2 supercell of Silicon")
    st.code("Get forces for bulk Gold (Au)")
    st.code("Generate FCC Aluminum with 3x3x3 supercell")
    st.code("Create BCC Iron structure")
    st.code("Calculate energy for NaCl (rocksalt)")
    st.code("Generate GaN zincblende structure")
    st.code("Create HCP Titanium with a=2.95")
    st.divider()
    st.markdown("**Supported:** Elements (Si, Al, Au, Fe, Ti, Mg, etc.), Compounds (NaCl, GaN, TiO2, etc.)")
    st.markdown("**Structures:** FCC, BCC, HCP, Diamond, Zincblende, Rocksalt, Wurtzite, Perovskite")
    st.divider()
    st.markdown("### External Sources:")
    st.code("Fetch from Materials Project: mp-149")
    st.code("Fetch from COD: cod-2000001")
    st.code("Load from URL: https://example.com/structure.cif")
    st.code("Load from file: /path/to/structure.cif")
    st.divider()
    st.markdown("### LLM Generation:")
    st.code("Create a 2x2x2 supercell of diamond cubic silicon")
    st.code("Generate FCC aluminum with lattice parameter 4.05")
    st.code("Make a rocksalt structure of sodium chloride")
    st.code("Generate MoS2 monolayer with AB stacking")
    st.code("Create perovskite BaTiO3 with a=4.00")
    st.info("💡 Enable 'Use LLM' checkbox for complex natural language descriptions")
    st.markdown("**See COMPLEX_STRUCTURES.md for advanced examples**")
    st.divider()
    
    # Debugging Section
    if debug_mode:
        st.markdown("### 🐛 Debug Tools")
        st.markdown("**Backend Console:** Check terminal where `python backend.py` is running")
        st.markdown("**Test Script:** Run `python test_structure.py`")
        st.markdown("**Guide:** See `DEBUG_GUIDE.md`")
        st.divider()
    
    st.info("Ensure your FastAPI backend is running on port 8000.")

# --- Main Layout ---
col1, col2 = st.columns([3, 2])

# === COLUMN 1: Chat Interface ===
with col1:
    st.markdown("<h1 style='text-align: center;'>ChatMat</h1>", unsafe_allow_html=True)
    
    # 1. Chat History Display
    st.markdown('<div class="chat-history-wrapper">', unsafe_allow_html=True)
    for role, text in st.session_state.history:
        if role == "user":
            st.markdown(f'<div class="chat-container user-msg">👤 You: {text}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-container bot-msg">🤖 ChatMat: {text}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 2. Input Area
    with st.form(key="chat_form", clear_on_submit=True):
        # First row: Input field
        user_input = st.text_input("", placeholder="e.g., Energy of bulk Silicon", label_visibility="collapsed")
        
        # Second row: Agent dropdown and space for other elements (like Cursor)
        col_dropdown, col_other = st.columns([1, 4])
        with col_dropdown:
            # Custom lightweight select (avoids Streamlit BaseWeb height)
            if "agent_option" not in st.session_state:
                st.session_state.agent_option = "Agent"
            agent_default = st.session_state.agent_option
            agent_options = ["Agent", "openai", "anthropic", "ollama"]
            # agent_icons = {
            #     "Agent": "🤖",
            #     "openai": "🟢",
            #     "anthropic": "🟣",
            #     "ollama": "🟡",
            # }
            options_html = "".join(
                f'<option value="{opt}" {"selected" if opt == agent_default else ""}>{opt}</option>'
                for opt in agent_options
            )
            custom_select = f"""
                <div style="height:30px; min-height:30px; padding:0; margin:0; display:flex; align-items:flex-start;">
                    <select id="agentSelect" style="
                        width: 100%;
                        height: 20px;
                        min-height: 20px;
                        line-height: 20px;
                        padding: 0 6px;
                        font-size: 0.9rem;
                        border: 1px solid #d3d3d3;
                        border-radius: 4px;
                        background: #f0f2f6;
                        box-sizing: border-box;
                        margin: 0;
                        display: block;
                    ">
                        {options_html}
                    </select>
                </div>
                <script src="https://unpkg.com/streamlit-component-lib@1.5.2/dist/index.js"></script>
                <script>
                    const selectEl = document.getElementById("agentSelect");
                    const send = () => Streamlit.setComponentValue(selectEl.value);
                    selectEl.addEventListener("change", send);
                    // Initialize value on load
                    send();
                </script>
            """
            agent_option_raw = components.html(custom_select, height=30, scrolling=False)
            
            # Extract actual value from agent_option (handle Streamlit objects)
            agent_option = None
            if agent_option_raw is not None:
                # If it's a string, use it directly
                if isinstance(agent_option_raw, str):
                    agent_option = agent_option_raw
                # If it's a number, convert to string
                elif isinstance(agent_option_raw, (int, float)):
                    agent_option = str(agent_option_raw)
                # If it's a Streamlit object, try to get value from session state
                else:
                    # Fall back to session state
                    agent_option = st.session_state.get("agent_option", "Agent")
            else:
                agent_option = st.session_state.get("agent_option", "Agent")
            
            # Ensure it's a valid option
            valid_options = ["Agent", "openai", "anthropic", "ollama"]
            if agent_option not in valid_options:
                agent_option = "Agent"
            
            # Store in session state
            st.session_state.agent_option = agent_option
        with col_other:
            pass  # Space for other elements
        
        # Get the actual agent option from session state to ensure it's a string
        # Always use session state to avoid DeltaGenerator objects
        agent_option = st.session_state.get("agent_option", "Agent")
        if not isinstance(agent_option, str):
            agent_option = "Agent"
            st.session_state.agent_option = "Agent"
        
        use_llm = (agent_option != "Agent")
        llm_provider = agent_option if (use_llm and agent_option in ["openai", "anthropic", "ollama"]) else None
        
        # Form submits on Enter key press - button is hidden
        submit_button = st.form_submit_button(use_container_width=True, label="", help="Press Enter to submit")

    # 3. Enhanced Natural Language Parser
    def parse_material_request(text: str) -> dict:
        """Parse natural language input to extract material, supercell, structure type, etc."""
        text_lower = text.lower()
        
        # Initialize defaults
        result = {
            "material_name": "Si",
            "supercell_dims": [1, 1, 1],
            "structure_type": None,
            "lattice_parameter": None,
            "compound": None,
            "source_type": None,
            "source_params": {},
            "use_llm": False,
            "llm_provider": None,
            "llm_params": {}
        }
        
        # Extract supercell dimensions (e.g., "2x2x2", "3x3x3", "2 2 2")
        supercell_patterns = [
            r'(\d+)\s*[x×]\s*(\d+)\s*[x×]\s*(\d+)',  # 2x2x2, 3×3×3
            r'supercell\s*[:\s]+(\d+)\s*[x×,]\s*(\d+)\s*[x×,]\s*(\d+)',  # supercell: 2x2x2
            r'(\d+)\s+(\d+)\s+(\d+)',  # 2 2 2 (if near "supercell")
        ]
        
        for pattern in supercell_patterns:
            match = re.search(pattern, text_lower)
            if match:
                result["supercell_dims"] = [int(match.group(1)), int(match.group(2)), int(match.group(3))]
                break
        
        # Extract structure types
        structure_keywords = {
            "fcc": ["fcc", "face-centered cubic", "face centered cubic"],
            "bcc": ["bcc", "body-centered cubic", "body centered cubic"],
            "hcp": ["hcp", "hexagonal close-packed", "hexagonal close packed"],
            "diamond": ["diamond", "diamond cubic"],
            "sc": ["sc", "simple cubic"],
            "zincblende": ["zincblende", "zinc blende", "sphalerite"],
            "rocksalt": ["rocksalt", "rock salt", "nacl structure"],
            "wurtzite": ["wurtzite"],
            "perovskite": ["perovskite"],
            "rutile": ["rutile"]
        }
        
        for struct_type, keywords in structure_keywords.items():
            if any(kw in text_lower for kw in keywords):
                result["structure_type"] = struct_type
                break
        
        # Extract lattice parameter (e.g., "a=5.43", "lattice 4.08")
        lattice_patterns = [
            r'[al]\s*=\s*([\d.]+)',
            r'lattice\s*(?:parameter|constant)?\s*[:=]?\s*([\d.]+)',
            r'a\s*=\s*([\d.]+)'
        ]
        for pattern in lattice_patterns:
            match = re.search(pattern, text_lower)
            if match:
                result["lattice_parameter"] = float(match.group(1))
                break
        
        # Define common words to filter out (used in multiple places)
        common_words = {"The", "For", "Get", "Calculate", "Energy", "Force", "Structure", 
                      "Supercell", "Bulk", "Of", "A", "An", "In", "On", "At"}
        
        # IMPORTANT: Check compounds FIRST before elements to avoid false matches
        # Extract compounds (e.g., "NaCl", "GaN", "TiO2", "sodium chloride")
        compound_map = {
            "nacl": {"name": "NaCl", "compound": ["Na", "Cl"]},
            "sodium chloride": {"name": "NaCl", "compound": ["Na", "Cl"]},
            "mgo": {"name": "MgO", "compound": ["Mg", "O"]},
            "magnesium oxide": {"name": "MgO", "compound": ["Mg", "O"]},
            "gan": {"name": "GaN", "compound": ["Ga", "N"]},
            "gallium nitride": {"name": "GaN", "compound": ["Ga", "N"]},
            "gap": {"name": "GaP", "compound": ["Ga", "P"]},
            "gallium phosphide": {"name": "GaP", "compound": ["Ga", "P"]},
            "zns": {"name": "ZnS", "compound": ["Zn", "S"]},
            "zinc sulfide": {"name": "ZnS", "compound": ["Zn", "S"]},
            "tio2": {"name": "TiO2", "compound": ["Ti", "O"]},
            "titanium dioxide": {"name": "TiO2", "compound": ["Ti", "O"]},
            "sio2": {"name": "SiO2", "compound": ["Si", "O"], "structure_type": "quartz"},
            "silicon dioxide": {"name": "SiO2", "compound": ["Si", "O"], "structure_type": "quartz"},
            "quartz": {"name": "SiO2", "compound": ["Si", "O"], "structure_type": "quartz"},
            "catio3": {"name": "CaTiO3", "compound": ["Ca", "Ti", "O"]},
            "calcium titanate": {"name": "CaTiO3", "compound": ["Ca", "Ti", "O"]},
        }
        
        for key, value in compound_map.items():
            if key in text_lower:
                result["material_name"] = value["name"]
                result["compound"] = value["compound"]
                # Set structure type if specified in compound_map
                if "structure_type" in value:
                    result["structure_type"] = value["structure_type"]
                break
        
        # Check for compound formulas (e.g., "NaCl", "GaN", "SiO2")
        # Only do this if we haven't already found a compound
        if not result.get("compound"):
            compound_pattern = r'\b([A-Z][a-z]?[A-Z]?[a-z]?\d*)\b'
            compound_matches = re.findall(compound_pattern, text)
            for match in compound_matches:
                if len(match) >= 2 and match not in common_words:
                    # Try to parse as compound (simple heuristic)
                    if any(c.isdigit() for c in match):  # Has numbers, likely compound (e.g., SiO2, TiO2)
                        result["material_name"] = match
                        # Try to extract elements (simplified)
                        elements = re.findall(r'[A-Z][a-z]?', match)
                        if len(elements) >= 2:
                            result["compound"] = elements
                            break  # Found a compound, stop looking
                    elif len(match) == 2 and match[0].isupper() and match[1].isupper():  # Like "GaN"
                        result["material_name"] = match
                        result["compound"] = [match[0], match[1]]
                        break  # Found a compound, stop looking
        
        # Only check for elements if we haven't found a compound
        if not result.get("compound"):
            # Extract material names (elements)
            # Common element names
            element_map = {
                "silicon": "Si", "si": "Si",
                "aluminum": "Al", "aluminium": "Al", "al": "Al",
                "gold": "Au", "au": "Au",
                "copper": "Cu", "cu": "Cu",
                "iron": "Fe", "fe": "Fe",
                "titanium": "Ti", "ti": "Ti",
                "magnesium": "Mg", "mg": "Mg",
                "nickel": "Ni", "ni": "Ni",
                "zinc": "Zn", "zn": "Zn",
                "carbon": "C", "c": "C",
                "germanium": "Ge", "ge": "Ge",
                "chromium": "Cr", "cr": "Cr",
                "molybdenum": "Mo", "mo": "Mo",
                "tungsten": "W", "w": "W",
                "vanadium": "V", "v": "V",
                "cobalt": "Co", "co": "Co",
                "palladium": "Pd", "pd": "Pd",
                "platinum": "Pt", "pt": "Pt",
                "silver": "Ag", "ag": "Ag",
                "beryllium": "Be", "be": "Be",
                "zirconium": "Zr", "zr": "Zr",
            }
            
            # Check for element names
            for name, symbol in element_map.items():
                if name in text_lower:
                    result["material_name"] = symbol
                    break
            
            # Check for chemical symbols directly (e.g., "Si", "Au", "Fe")
            # Only if we still don't have a material name
            if result["material_name"] == "Si":  # Still default
                element_symbols = r'\b([A-Z][a-z]?)\b'
                matches = re.findall(element_symbols, text)
                if matches:
                    # Filter out common words that aren't elements
                    potential_elements = [m for m in matches if m not in common_words and len(m) <= 2]
                    if potential_elements:
                        result["material_name"] = potential_elements[0]
        
        # Detect external source types (check after compounds to avoid conflicts)
        # Materials Project (mp-XXXX)
        if re.search(r'\bmp-\d+\b', text, re.IGNORECASE):
            match = re.search(r'\b(mp-\d+)\b', text, re.IGNORECASE)
            if match:
                result["material_name"] = match.group(1)
                result["source_type"] = "mp"
        
        # COD database (cod-XXXXXXX or just numbers)
        elif re.search(r'\bcod-?\d+\b', text, re.IGNORECASE):
            match = re.search(r'\bcod-?(\d+)\b', text, re.IGNORECASE)
            if match:
                result["material_name"] = match.group(1)
                result["source_type"] = "cod"
        
        # URL detection
        elif re.search(r'https?://\S+', text):
            match = re.search(r'(https?://\S+)', text)
            if match:
                result["material_name"] = match.group(1)
                result["source_type"] = "url"
        
        # File path detection (if it looks like a path)
        elif re.search(r'[/\\]', text) or text.endswith(('.cif', '.xyz', '.vasp', '.poscar')):
            result["material_name"] = text.strip()
            result["source_type"] = "file"
        
        return result
    
    # 3. Logic Handling
    if submit_button and user_input:
        # Add user message to history
        st.session_state.history.append(("user", user_input))
        
        # Parse the user input
        parsed = parse_material_request(user_input)
        
        # Determine if we should use LLM
        # Use LLM if checkbox is checked OR if the description is complex (long, contains multiple clauses)
        should_use_llm = use_llm or (len(user_input.split()) > 10 and not parsed.get("source_type"))
        
        # Prepare payload for backend - ensure all values are JSON-serializable
        # Convert Streamlit objects to plain Python types
        # Get llm_provider from session state to avoid DeltaGenerator objects
        agent_option_safe = st.session_state.get("agent_option", "Agent")
        if not isinstance(agent_option_safe, str):
            agent_option_safe = "Agent"
        
        llm_provider_str = None
        if should_use_llm:
            # Use the safe agent option from session state
            if agent_option_safe in ["openai", "anthropic", "ollama"]:
                llm_provider_str = agent_option_safe
            else:
                # Fallback: try to extract from llm_provider if it's a string
                if isinstance(llm_provider, str) and llm_provider in ["openai", "anthropic", "ollama"]:
                    llm_provider_str = llm_provider
                else:
                    llm_provider_str = None
        
        # Ensure all values are JSON-serializable (no Streamlit objects)
        lattice_param = None
        if parsed["lattice_parameter"] is not None:
            try:
                lattice_param = float(parsed["lattice_parameter"])
            except (ValueError, TypeError):
                lattice_param = None
        
        payload = {
            "intent": "CALCULATE",
            "material_name": str(parsed["material_name"]) if parsed["material_name"] else "Si",
            "user_input": str(user_input) if user_input else None,
            "structure_details": {
                "supercell_dims": [int(x) for x in parsed["supercell_dims"]],
                "structure_type": str(parsed["structure_type"]) if parsed["structure_type"] else None,
                "lattice_parameter": lattice_param,
                "compound": [str(x) for x in parsed["compound"]] if parsed["compound"] else None,
                "source_type": str(parsed.get("source_type")) if parsed.get("source_type") else None,
                "source_params": {str(k): str(v) if not isinstance(v, (dict, list)) else v 
                                 for k, v in parsed.get("source_params", {}).items()} if parsed.get("source_params") else {},
                "use_llm": bool(should_use_llm),
                "llm_provider": llm_provider_str,
                "llm_params": {
                    "model": "gpt-4o-mini" if llm_provider_str == "openai" else 
                            "claude-3-haiku-20240307" if llm_provider_str == "anthropic" else
                            "llama3" if llm_provider_str == "ollama" else None
                } if should_use_llm and llm_provider_str else {}
            }
        }

        with st.spinner("Synthesizing structure and calculating physics..."):
            try:
                response = requests.post(BACKEND_URL, json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Format the result message
                    material_display = data.get('material', parsed["material_name"])
                    n_atoms = data.get('n_atoms', 'N/A')
                    supercell_str = f"{parsed['supercell_dims'][0]}×{parsed['supercell_dims'][1]}×{parsed['supercell_dims'][2]}"
                    structure_info = f" ({parsed['structure_type'].upper()})" if parsed['structure_type'] else ""
                    
                    result_msg = (
                        f"**Structure:** {material_display}{structure_info}\n\n"
                        f"📦 **Supercell:** {supercell_str}\n"
                        f"🔢 **Atoms:** {n_atoms}\n\n"
                        f"⚡ **Total Energy:** {data.get('energy', 'N/A'):.4f} eV\n\n"
                        f"💪 **Max Force:** {data.get('max_force', 'N/A'):.4f} eV/Å"
                    )
                    
                    st.session_state.history.append(("bot", result_msg))
                    
                    # Save XYZ data for visualization
                    if "structure_xyz" in data:
                        xyz_data = data["structure_xyz"]
                        # Debug: Check XYZ data
                        xyz_lines = [line for line in xyz_data.strip().split('\n') if line.strip()]
                        if len(xyz_lines) > 0:
                            try:
                                num_atoms = int(xyz_lines[0].strip())
                                backend_atoms = data.get('n_atoms', 'N/A')
                                
                                if debug_mode:
                                    st.info(f"📊 **Debug Info:**")
                                    st.write(f"- Received structure with **{num_atoms} atoms** (backend: {backend_atoms})")
                                    st.write(f"- Material: {data.get('material', 'N/A')}")
                                    st.write(f"- Energy: {data.get('energy', 'N/A'):.4f} eV")
                                    
                                    if num_atoms == 1:
                                        st.error("⚠️ **WARNING: Structure has only 1 atom!** Check backend logs.")
                                    
                                    # Show XYZ preview
                                    with st.expander("🔍 View XYZ Data"):
                                        st.code(xyz_data[:1000], language=None)  # First 1000 chars
                                    
                                    # Show parsed request
                                    with st.expander("🔍 View Parsed Request"):
                                        st.json(parsed)
                                    
                                    # Show full response
                                    with st.expander("🔍 View Full Response"):
                                        st.json(data)
                                else:
                                    if num_atoms == 1:
                                        st.warning("⚠️ Only 1 atom detected. Enable Debug Mode for details.")
                                    
                            except ValueError:
                                if debug_mode:
                                    st.warning(f"⚠️ Could not parse atom count. First line: {xyz_lines[0]}")
                        st.session_state.last_structure_xyz = xyz_data
                        
                else:
                    # Try to get error details from response
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("detail", f"HTTP {response.status_code}")
                        if isinstance(error_detail, list) and len(error_detail) > 0:
                            error_detail = error_detail[0].get("msg", str(error_detail[0]))
                    except:
                        error_detail = f"HTTP {response.status_code}: {response.text[:200]}"
                    
                    st.error(f"Backend Error: {error_detail}")
                    st.session_state.history.append(("bot", f"❌ Error: {error_detail}"))
            
            except requests.exceptions.ConnectionError as e:
                st.error(f"Connection Failed: Cannot connect to backend at {BACKEND_URL}")
                st.session_state.history.append(("bot", "❌ Backend is offline. Please ensure the backend is running on port 8000."))
            except requests.exceptions.Timeout as e:
                st.error(f"Request Timeout: Backend took too long to respond")
                st.session_state.history.append(("bot", "❌ Request timeout. The backend may be overloaded."))
            except requests.exceptions.RequestException as e:
                st.error(f"Request Error: {e}")
                st.session_state.history.append(("bot", f"❌ Request Error: {str(e)}"))
            except Exception as e:
                st.error(f"Unexpected Error: {e}")
                if debug_mode:
                    import traceback
                    st.code(traceback.format_exc())
                st.session_state.history.append(("bot", f"❌ Error: {str(e)}"))
        
        # Rerun to update chat history immediately
        st.rerun()

# === COLUMN 2: 3D Visualization ===
with col2:
    # st.subheader("🧊 Structure Visualizer")
    st.subheader("🧊 Visualizer")

    if st.session_state.last_structure_xyz:
        # Create a 3D view using py3Dmol
        xyz_data = st.session_state.last_structure_xyz
        
        # Debug: Show XYZ info
        xyz_lines = [line for line in xyz_data.strip().split('\n') if line.strip()]
        if len(xyz_lines) > 0:
            try:
                num_atoms_xyz = int(xyz_lines[0].strip())
                if debug_mode:
                    st.caption(f"📊 **Visualizer Debug:** XYZ file contains {num_atoms_xyz} atoms")
                    if num_atoms_xyz == 1:
                        st.error("⚠️ **CRITICAL: Only 1 atom in XYZ!** Structure generation failed.")
                    # Count unique elements
                    if len(xyz_lines) > 2:
                        elements_in_xyz = set()
                        for line in xyz_lines[2:2+num_atoms_xyz]:
                            if line.strip():
                                parts = line.split()
                                if len(parts) > 0:
                                    elements_in_xyz.add(parts[0])
                        st.caption(f"   Elements found: {elements_in_xyz}")
                else:
                    if num_atoms_xyz == 1:
                        st.warning("⚠️ Only 1 atom detected. Enable Debug Mode for details.")
            except Exception as e:
                if debug_mode:
                    st.warning(f"⚠️ Could not parse XYZ: {e}")
        
        # Debug: Verify XYZ data before visualization
        if debug_mode:
            xyz_preview = xyz_data[:500] if len(xyz_data) > 500 else xyz_data
            with st.expander("🔍 XYZ Data for Visualization"):
                st.code(xyz_preview, language=None)
                st.write(f"Total length: {len(xyz_data)} characters")
        
        try:
            view = py3Dmol.view(width=400, height=400)
            view.addModel(xyz_data, "xyz")
            view.setStyle({'sphere': {'scale': 0.3}, 'stick': {}})
            view.zoomTo()
            view.setBackgroundColor('white')
            
            # Render the molecule
            showmol(view, height=400, width=400)
            
            if debug_mode:
                st.success("✅ Visualization rendered successfully")
        except Exception as e:
            st.error(f"❌ Visualization error: {e}")
            if debug_mode:
                st.code(f"XYZ data that failed:\n{xyz_data[:500]}", language=None)
        
        st.caption("Interactive 3D View: Click and drag to rotate.")
        
        # Download Button
        st.download_button(
            label="Download .XYZ File",
            data=xyz_data,
            file_name="structure.xyz",
            mime="chemical/x-xyz"
        )
    else:
        st.info("Generate a structure to see it here.")
        # Placeholder image for visual appeal before generation
        st.markdown("*(Example: Diamond structure)*") 
