"""Agent Chat UI adapter (Playwright) — allowlisted chat box only.

Default OFF via flags.enable_agent_chat_ui. This is NOT a generic web
XSS/SQLi pack — only the configured chat selectors on allowlisted hosts.
"""

from __future__ import annotations

from typing import Any

from enhanced_harness.safety import SafetyError, assert_url_allowed
from enhanced_harness.scope import AgentChatUITarget, Scope


class AgentChatUIAdapter:
    """Drive an allowlisted AI chat page via Playwright."""

    def __init__(self, target: AgentChatUITarget, scope: Scope) -> None:
        self.target = target
        self.scope = scope
        self._pw = None
        self._browser = None
        self._page = None
        self.page_title: str = ""
        self.ready: bool = False

    async def connect(self) -> None:
        if not self.scope.flags.enable_agent_chat_ui:
            raise SafetyError(
                "Agent Chat UI adapter refused: flags.enable_agent_chat_ui is false"
            )
        assert_url_allowed(self.target.url, self.scope)
        try:
            from playwright.async_api import async_playwright
        except ImportError as e:
            raise SafetyError(
                "Playwright not installed. Run: pip install -e '.[chat]' "
                "&& playwright install chromium"
            ) from e

        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=True)
        self._page = await self._browser.new_page()
        await self._page.goto(self.target.url, wait_until="domcontentloaded")
        await self._page.wait_for_selector(self.target.input_selector, timeout=10000)
        await self._page.wait_for_selector(self.target.send_selector, timeout=10000)
        self.page_title = await self._page.title()
        self.ready = True

    async def observe(self) -> dict[str, Any]:
        assert self._page is not None
        assert_url_allowed(self.target.url, self.scope)
        has_input = await self._page.locator(self.target.input_selector).count()
        has_send = await self._page.locator(self.target.send_selector).count()
        has_messages = await self._page.locator(self.target.messages_selector).count()
        return {
            "target": self.target.name,
            "url": self.target.url,
            "title": self.page_title,
            "ready": self.ready,
            "selectors": {
                "input": self.target.input_selector,
                "send": self.target.send_selector,
                "messages": self.target.messages_selector,
                "input_count": has_input,
                "send_count": has_send,
                "messages_count": has_messages,
            },
        }

    async def send_message(self, text: str) -> dict[str, Any]:
        """Type into the allowlisted chat box and capture assistant reply text."""
        assert self._page is not None
        if not self.scope.flags.enable_agent_chat_ui:
            raise SafetyError("enable_agent_chat_ui is false")
        assert_url_allowed(self.target.url, self.scope)

        before = await self.read_messages()
        before_count = len(before)

        await self._page.fill(self.target.input_selector, text)
        await self._page.click(self.target.send_selector)

        # Wait for a new bot message (or any new message node)
        try:
            await self._page.wait_for_function(
                """([sel, n]) => document.querySelector(sel)
                    && document.querySelector(sel).querySelectorAll('.msg, [data-role], .message, li, p').length > n""",
                arg=[self.target.messages_selector, before_count],
                timeout=10000,
            )
        except Exception:  # noqa: BLE001 — fall through to read whatever is there
            await self._page.wait_for_timeout(500)

        after = await self.read_messages()
        new_msgs = after[before_count:] if len(after) > before_count else after[-2:]
        bot_text = "\n".join(
            m["text"] for m in new_msgs if m.get("role") in {"bot", "assistant", "ai"}
        )
        if not bot_text:
            bot_text = "\n".join(m["text"] for m in new_msgs)

        return {
            "sent": text,
            "reply": bot_text,
            "messages": after,
        }

    async def read_messages(self) -> list[dict[str, str]]:
        assert self._page is not None
        return await self._page.eval_on_selector_all(
            f"{self.target.messages_selector} .msg, "
            f"{self.target.messages_selector} [data-role], "
            f"{self.target.messages_selector} .message",
            """els => els.map(el => ({
                role: el.dataset.role || (el.classList.contains('user') ? 'user'
                      : el.classList.contains('bot') ? 'bot' : 'unknown'),
                text: (el.innerText || el.textContent || '').trim()
            }))""",
        )

    async def close(self) -> None:
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._pw is not None:
            await self._pw.stop()
            self._pw = None
        self._page = None
        self.ready = False
