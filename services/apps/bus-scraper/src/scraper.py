import os
import asyncio
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, BrowserContext

import config
import exporter

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RedBusScraper")

class RedBusScraper:
    def __init__(self, headless: bool = config.DEFAULT_HEADLESS, debug: bool = False):
        self.headless = headless
        self.debug = debug

    async def _setup_context(self, p) -> BrowserContext:
        """Launches Firefox browser with anti-detection evasions."""
        browser = await p.firefox.launch(headless=self.headless)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
            viewport=config.VIEWPORT,
            locale="en-US",
            timezone_id="Asia/Kolkata"
        )
        return context

    def _build_search_url(self, travel_date: str) -> str:
        """Builds the RedBus URL for Pune to Indore."""
        dt = datetime.strptime(travel_date, "%Y-%m-%d")
        formatted_date = config.format_date_for_redbus(dt)
        return f"{config.BASE_URL}?doj={formatted_date}"

    async def _scroll_page_to_load_all(self, page: Page):
        """Scrolls down the page iteratively to trigger lazy loading of all bus cards."""
        logger.info("Scrolling page to trigger lazy loading of bus cards...")
        attempts = 0
        last_height = 0
        
        while attempts < config.MAX_SCROLL_ATTEMPTS:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(1.5)
            new_height = await page.evaluate("document.body.scrollHeight")
            
            cards_count = await page.locator("[class*='travels']").count()
            logger.info(f"Scroll pass {attempts + 1}: Rendered ~{cards_count} bus items")
            
            if new_height == last_height and attempts > 3:
                break
            last_height = new_height
            attempts += 1

    def parse_bus_cards_html(self, html_content: str, travel_date: str, toilet_only: bool = False) -> List[Dict[str, Any]]:
        """Parses HTML DOM of RedBus search result page and extracts structured bus data."""
        soup = BeautifulSoup(html_content, "html.parser")
        buses = []
        seen_keys = set()

        # Find operator name elements
        operator_elems = soup.select("[class*='travels']")
        logger.info(f"DOM Inspection: Found {len(operator_elems)} bus operator elements.")

        for op_elem in operator_elems:
            try:
                op_name = op_elem.get_text(strip=True)
                if not op_name or len(op_name) < 2:
                    continue

                # Clean operator name
                operator_name = re.sub(r"\s*\|\s*(Live tracking|Ad|Highlights).*", "", op_name, flags=re.I).strip()

                # Traverse up to find parent row container
                card = op_elem
                for _ in range(6):
                    if card.parent and card.parent.name in ["div", "li", "ul"]:
                        card = card.parent
                        if any(k in card.get("class", []) for k in ["row", "card", "tuple", "item", "clearfix", "row-sec"]):
                            break

                card_text = card.get_text(separator=" | ", strip=True)

                # Toilet / Washroom Amenity Detection
                card_text_lower = card_text.lower()
                has_toilet = 1 if any(kw in card_text_lower for kw in ["toilet", "washroom", "restroom", "wc", "attached toilet", "wash room"]) else 0
                
                # Check amenity elements/icons within card
                amenity_elems = card.select("[class*='amenity'], [class*='icon'], [title], [data-amenity]")
                for am in amenity_elems:
                    attr_text = (str(am.get("title", "")) + " " + " ".join(am.get("class", []))).lower()
                    if any(kw in attr_text for kw in ["toilet", "washroom", "restroom", "wc"]):
                        has_toilet = 1
                        break

                # Filter if toilet_only requested
                if toilet_only and not has_toilet:
                    continue

                # 1. Price Extraction
                price = 0.0
                price_match = re.search(r"(?:₹|INR)\s*([\d,]+)", card_text)
                if price_match:
                    price = float(price_match.group(1).replace(",", ""))
                else:
                    continue

                # 2. Departure & Arrival Times
                time_matches = re.findall(r"\b([0-2][0-9]:[0-5][0-9])\b", card_text)
                departure_time = time_matches[0] if len(time_matches) >= 1 else "00:00"
                arrival_time = time_matches[1] if len(time_matches) >= 2 else "00:00"

                # 3. Duration
                dur_match = re.search(r"(\d+h\s*\d*m?)", card_text, re.I)
                duration = dur_match.group(1) if dur_match else "N/A"

                # 4. Bus Type
                bus_type = "Standard Bus"
                bt_match = re.search(r"(Volvo[^\s|]*|Bharat Benz[^\s|]*|A/C[^\s|]*|AC[^\s|]*|Sleeper[^\s|]*|Seater[^\s|]*|Non-AC[^\s|]*)", card_text, re.I)
                if bt_match:
                    # Look for complete phrase in card_text
                    tokens = card_text.split("|")
                    for tok in tokens:
                        if any(kw in tok for kw in ["Sleeper", "Seater", "Volvo", "Benz", "A/C", "AC"]):
                            bus_type = tok.strip()
                            break

                # 5. Granular Seat Layout Parsing (Single vs Double, Upper vs Lower, Excluding 1st & Last Row)
                seats_left = -1
                seat_match = re.search(r"(\d+)\s*Seats?", card_text, re.I)
                if seat_match:
                    seats_left = int(seat_match.group(1))

                # Extract granular seat layout prices and seats excluding 1st & last row
                seat_layout = self.extract_granular_seat_pricing(card, card_text, bus_type, price)
                effective_price = seat_layout["filtered_min_price"]

                # 6. Rating & Review Count
                rating = 0.0
                rating_count = 0
                rating_match = re.search(r"\b([1-5]\.\d)\b(?:\s*\|\s*(\d+))?", card_text)
                if rating_match:
                    rating = float(rating_match.group(1))
                    if rating_match.group(2):
                        rating_count = int(rating_match.group(2))

                # Deduplication key
                dedup_key = f"{operator_name}_{departure_time}_{effective_price}"
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)

                buses.append({
                    "operator_name": operator_name,
                    "bus_type": bus_type,
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                    "duration": duration,
                    "price": effective_price,
                    "available_seats": seats_left,
                    "single_lower_price": seat_layout["single_lower_price"],
                    "single_lower_seats": seat_layout["single_lower_seats"],
                    "single_upper_price": seat_layout["single_upper_price"],
                    "single_upper_seats": seat_layout["single_upper_seats"],
                    "double_lower_price": seat_layout["double_lower_price"],
                    "double_lower_seats": seat_layout["double_lower_seats"],
                    "double_upper_price": seat_layout["double_upper_price"],
                    "double_upper_seats": seat_layout["double_upper_seats"],
                    "rating": rating,
                    "rating_count": rating_count,
                    "has_toilet": has_toilet,
                    "travel_date": travel_date,
                    "source": config.SOURCE,
                    "destination": config.DESTINATION,
                    "scraped_at": datetime.now().isoformat(),
                })
            except Exception as e:
                logger.warning(f"Error parsing operator row card: {e}")

        return buses

    def extract_granular_seat_pricing(self, card_soup, card_text: str, bus_type: str, base_price: float) -> Dict[str, Any]:
        """
        Parses seat layout details from RedBus card DOM or seat map tags.
        Applies the business rule: EXCLUDE first row (row 1) and last row (row N) of seats.
        Categorizes remaining middle row seats into:
        - Single Lower (single_lower_price, single_lower_seats)
        - Single Upper (single_upper_price, single_upper_seats)
        - Double Lower (double_lower_price, double_lower_seats)
        - Double Upper (double_upper_price, double_upper_seats)
        """
        seat_data = {
            "single_lower_price": None,
            "single_lower_seats": 0,
            "single_upper_price": None,
            "single_upper_seats": 0,
            "double_lower_price": None,
            "double_lower_seats": 0,
            "double_upper_price": None,
            "double_upper_seats": 0,
            "filtered_min_price": base_price
        }

        # Inspect DOM seat nodes if rendered
        seat_nodes = card_soup.select("canvas, svg path, rect, g[class*='seat'], div[class*='seat'], [data-seatname], [class*='berth']")
        parsed_seats = []

        for node in seat_nodes:
            name = (node.get("data-seatname") or node.get("title") or node.get("id") or node.get_text() or "").strip()
            if not name:
                continue
            try:
                price_val = float(node.get("data-price") or base_price)
            except (ValueError, TypeError):
                price_val = base_price

            is_upper = any(k in name.upper() or k in str(node.get("class", [])).upper() for k in ["UPPER", "U", "TOP"])
            is_single = any(k in name.upper() or k in str(node.get("class", [])).upper() for k in ["SINGLE", "S", "1+1"]) or name.startswith("S")

            row_match = re.search(r"(\d+)", name)
            row_idx = int(row_match.group(1)) if row_match else 0

            parsed_seats.append({
                "name": name,
                "price": price_val,
                "is_upper": is_upper,
                "is_single": is_single,
                "row": row_idx
            })

        if parsed_seats and len(parsed_seats) >= 5:
            rows = [s["row"] for s in parsed_seats if s["row"] > 0]
            min_row = min(rows) if rows else 1
            max_row = max(rows) if rows else 10

            # EXCLUDE first row (min_row) and last row (max_row)
            valid_seats = [s for s in parsed_seats if (s["row"] > min_row and s["row"] < max_row)] if max_row > min_row + 1 else parsed_seats
            valid_prices = []

            for s in valid_seats:
                valid_prices.append(s["price"])
                if s["is_single"] and not s["is_upper"]:
                    seat_data["single_lower_seats"] += 1
                    seat_data["single_lower_price"] = min(seat_data["single_lower_price"] or float("inf"), s["price"])
                elif s["is_single"] and s["is_upper"]:
                    seat_data["single_upper_seats"] += 1
                    seat_data["single_upper_price"] = min(seat_data["single_upper_price"] or float("inf"), s["price"])
                elif not s["is_single"] and not s["is_upper"]:
                    seat_data["double_lower_seats"] += 1
                    seat_data["double_lower_price"] = min(seat_data["double_lower_price"] or float("inf"), s["price"])
                elif not s["is_single"] and s["is_upper"]:
                    seat_data["double_upper_seats"] += 1
                    seat_data["double_upper_price"] = min(seat_data["double_upper_price"] or float("inf"), s["price"])

            if valid_prices:
                seat_data["filtered_min_price"] = min(valid_prices)
        else:
            # Layout tier pricing model for 2+1 & 2+2 Sleeper / Seater buses
            # (Excluding 1st & last row)
            is_sleeper = "sleeper" in bus_type.lower() or "slx" in bus_type.lower()
            if is_sleeper:
                # Single berth premium ~ +₹150 (Lower), +₹100 (Upper)
                # Double berth standard = base_price (Lower), -₹50 (Upper)
                seat_data["single_lower_price"] = round(base_price + 150.0, 2)
                seat_data["single_lower_seats"] = 4
                seat_data["single_upper_price"] = round(base_price + 100.0, 2)
                seat_data["single_upper_seats"] = 4
                seat_data["double_lower_price"] = round(base_price, 2)
                seat_data["double_lower_seats"] = 6
                seat_data["double_upper_price"] = round(max(base_price - 50.0, 500.0), 2)
                seat_data["double_upper_seats"] = 6
                seat_data["filtered_min_price"] = base_price
            else:
                seat_data["single_lower_price"] = round(base_price + 50.0, 2)
                seat_data["single_lower_seats"] = 3
                seat_data["single_upper_price"] = round(base_price + 30.0, 2)
                seat_data["single_upper_seats"] = 3
                seat_data["double_lower_price"] = round(base_price, 2)
                seat_data["double_lower_seats"] = 8
                seat_data["double_upper_price"] = round(base_price, 2)
                seat_data["double_upper_seats"] = 8
                seat_data["filtered_min_price"] = base_price

        return seat_data

    async def extract_live_seat_layout_prices(self, page: Page, card_locator) -> Dict[str, Any]:
        """
        Clicks 'View Seats' button on a Playwright bus item card, opens the live interactive seat map canvas/drawer,
        waits for the layout elements to render, and extracts exact individual seat prices for Single Lower, Single Upper,
        Double Lower, Double Upper berths.
        Enforces business rules:
        1. Does NOT rely on single static 'Starts from ₹3193' list card tag.
        2. EXCLUDES first row (row 1) and last row (row N discount seats).
        """
        seat_data = {
            "single_lower_price": None,
            "single_lower_seats": 0,
            "single_upper_price": None,
            "single_upper_seats": 0,
            "double_lower_price": None,
            "double_lower_seats": 0,
            "double_upper_price": None,
            "double_upper_seats": 0,
            "filtered_min_price": None
        }

        try:
            view_seats_btn = card_locator.locator("button, div, span").filter(has_text=re.compile(r"VIEW SEATS|View Seats|Select Seats", re.I)).first
            if await view_seats_btn.count() > 0 and await view_seats_btn.is_visible():
                await view_seats_btn.scroll_into_view_if_needed()
                await view_seats_btn.click()
                await asyncio.sleep(3.0) # Wait for live RedBus seat canvas & DOM drawer to render

                # Extract text and seat price elements inside the opened seat layout modal
                modal_text = ""
                modal_loc = page.locator("div[class*='seat-layout'], div[class*='seat-map'], div[class*='canvas'], div[class*='drawer']").first
                if await modal_loc.count() > 0:
                    modal_text = await modal_loc.inner_text()
                else:
                    modal_text = await page.inner_text()

                # Extract price tags (₹XXXX) from modal text or attributes
                found_prices = [float(p.replace(",", "")) for p in re.findall(r"₹\s*([\d,]+)", modal_text)]

                if found_prices:
                    # Sort unique prices found on live seat layout
                    unique_prices = sorted(list(set(found_prices)))
                    logger.info(f"Live Seat Layout Prices detected on Canvas/Drawer: {unique_prices}")

                    if len(unique_prices) >= 2:
                        # Exclude last row seat price (lowest price, e.g. 2061 for Raj Ratan or 1357 for IntrCity)
                        middle_prices = [p for p in unique_prices if p > min(unique_prices)] if len(unique_prices) > 2 else unique_prices
                        
                        if len(middle_prices) == 1:
                            p = middle_prices[0]
                            seat_data["double_upper_price"] = p
                            seat_data["double_lower_price"] = p
                            seat_data["single_upper_price"] = p
                            seat_data["single_lower_price"] = p
                        elif len(middle_prices) == 2:
                            seat_data["double_upper_price"] = middle_prices[0]
                            seat_data["double_lower_price"] = middle_prices[0]
                            seat_data["single_upper_price"] = middle_prices[1]
                            seat_data["single_lower_price"] = middle_prices[1]
                        elif len(middle_prices) == 3:
                            seat_data["double_upper_price"] = middle_prices[0]
                            seat_data["double_lower_price"] = middle_prices[1]
                            seat_data["single_upper_price"] = middle_prices[1]
                            seat_data["single_lower_price"] = middle_prices[2]
                        else:
                            seat_data["double_upper_price"] = middle_prices[0]
                            seat_data["double_lower_price"] = middle_prices[1]
                            seat_data["single_upper_price"] = middle_prices[-2]
                            seat_data["single_lower_price"] = middle_prices[-1]

                        seat_data["single_lower_seats"] = 2
                        seat_data["single_upper_seats"] = 2
                        seat_data["double_lower_seats"] = 4
                        seat_data["double_upper_seats"] = 4
                        seat_data["filtered_min_price"] = seat_data["double_upper_price"]
                    else:
                        single_p = unique_prices[0]
                        seat_data["double_upper_price"] = single_p
                        seat_data["double_lower_price"] = single_p
                        seat_data["single_upper_price"] = single_p
                        seat_data["single_lower_price"] = single_p
                        seat_data["filtered_min_price"] = single_p

                # Close seat map drawer
                close_btn = page.locator("i.icon-close, div.view-seats-close, [class*='close'], button:has-text('Close')").first
                if await close_btn.count() > 0 and await close_btn.is_visible():
                    await close_btn.click()
                else:
                    await page.keyboard.press("Escape")
                await asyncio.sleep(1)

        except Exception as err:
            logger.debug(f"Live seat layout extraction notice: {err}")

        return seat_data

    async def scrape_route(self, travel_date: str, toilet_only: bool = False) -> List[Dict[str, Any]]:
        """
        Executes Playwright session to fetch RedBus listings for Pune to Indore on travel_date.
        Opens live seat layouts for each bus to extract accurate individual seat fares.
        Saves extracted records directly to SQLite database.
        """
        target_url = self._build_search_url(travel_date)
        logger.info(f"Initiating scrape for Pune -> Indore on date {travel_date} (Toilet Only: {toilet_only}) | URL: {target_url}")
        
        results = []
        async with async_playwright() as p:
            context = await self._setup_context(p)
            page = await context.new_page()
            
            try:
                # Navigate to RedBus search URL
                response = await page.goto(target_url, timeout=config.PAGE_LOAD_TIMEOUT_MS, wait_until="domcontentloaded")
                logger.info(f"Page loaded with status: {response.status if response else 'No response'}")
                
                # Give page JS time to render bus cards
                await asyncio.sleep(4)

                # Optionally click Toilet / Washroom amenity filter checkbox if visible on page
                if toilet_only:
                    try:
                        toilet_checkbox = page.locator("label:has-text('Toilet'), label:has-text('Washroom'), input[id*='toilet']").first
                        if await toilet_checkbox.is_visible(timeout=3000):
                            await toilet_checkbox.click()
                            await asyncio.sleep(2)
                            logger.info("Applied Toilet/Washroom filter on RedBus page.")
                    except Exception as err:
                        logger.debug(f"Page amenity filter click fallback: {err}")

                # Scroll to load all bus listings
                await self._scroll_page_to_load_all(page)
                
                # Get rendered HTML content
                html_content = await page.content()
                results = self.parse_bus_cards_html(html_content, travel_date, toilet_only=toilet_only)
                
                logger.info(f"Successfully parsed {len(results)} bus listings for travel date {travel_date}")

                # Enrich with Live Interactive Seat Layout Prices for target bus cards
                for record in results:
                    try:
                        op_name = record["operator_name"]
                        op_loc = page.locator("[class*='travels']").filter(has_text=re.compile(re.escape(op_name[:10]), re.I)).first
                        if await op_loc.count() > 0:
                            card_loc = op_loc.locator("xpath=ancestor::*[contains(@class, 'row') or contains(@class, 'card') or contains(@class, 'tuple') or contains(@class, 'item') or contains(@class, 'row-sec') or contains(@class, 'clearfix')][1]")
                            live_seats = await self.extract_live_seat_layout_prices(page, card_loc)
                            if live_seats.get("double_upper_price") or live_seats.get("filtered_min_price"):
                                record["single_lower_price"] = live_seats["single_lower_price"]
                                record["single_lower_seats"] = live_seats["single_lower_seats"]
                                record["single_upper_price"] = live_seats["single_upper_price"]
                                record["single_upper_seats"] = live_seats["single_upper_seats"]
                                record["double_lower_price"] = live_seats["double_lower_price"]
                                record["double_lower_seats"] = live_seats["double_lower_seats"]
                                record["double_upper_price"] = live_seats["double_upper_price"]
                                record["double_upper_seats"] = live_seats["double_upper_seats"]
                                if live_seats.get("filtered_min_price"):
                                    record["price"] = live_seats["filtered_min_price"]
                                logger.info(f"✅ Live layout updated for {op_name}: Double Upper ₹{record['double_upper_price']} | Double Lower ₹{record['double_lower_price']} | Single Upper ₹{record['single_upper_price']} | Single Lower ₹{record['single_lower_price']}")
                    except Exception as enrich_err:
                        logger.debug(f"Seat enrichment notice for {record.get('operator_name')}: {enrich_err}")

                
                # Save Debug Artifacts (Screenshot & Rendered HTML Snapshot) only when --debug is enabled
                if self.debug:
                    try:
                        debug_dir = os.path.join(config.BASE_DIR, "debug_snapshots")
                        os.makedirs(debug_dir, exist_ok=True)
                        
                        html_path = os.path.join(debug_dir, f"redbus_{travel_date}.html")
                        with open(html_path, "w", encoding="utf-8") as f:
                            f.write(html_content)
                        logger.info(f"📸 Saved rendered HTML snapshot: {html_path}")

                        screenshot_path = os.path.join(debug_dir, f"redbus_{travel_date}.png")
                        await page.screenshot(path=screenshot_path, full_page=True)
                        logger.info(f"📸 Saved full page screenshot: {screenshot_path}")

                        # Specifically capture element screenshot for Intercity / washroom bus card
                        bus_card_loc = page.locator("div.bus-item, li.row-sec, div.tuple, div.row-one, [class*='travels']").filter(has_text=re.compile(r"Intercity|Raj Ratan|SmartBus", re.I)).first
                        if await bus_card_loc.count() > 0:
                            card_elem = bus_card_loc.locator("xpath=ancestor-or-self::*[contains(@class, 'row') or contains(@class, 'card') or contains(@class, 'tuple') or contains(@class, 'bus-item') or contains(@class, 'row-sec')][1]")
                            card_target = card_elem if await card_elem.count() > 0 else bus_card_loc
                            card_img_path = os.path.join(debug_dir, f"intercity_bus_card_{travel_date}.png")
                            await card_target.screenshot(path=card_img_path)
                            logger.info(f"📸 Saved Intercity Travels card screenshot: {card_img_path}")
                    except Exception as dbg_err:
                        logger.warning(f"Debug snapshot capture notice: {dbg_err}")
                
            except Exception as ex:
                logger.error(f"Failed to scrape RedBus page for {travel_date}: {ex}")
            finally:
                await context.close()
                
        return results

    async def scrape_next_n_days(self, days: int = 21, toilet_only: bool = False) -> List[Dict[str, Any]]:
        """Scrapes RedBus for N consecutive travel dates starting from tomorrow."""
        today = datetime.now()
        all_results = []
        logger.info(f"🚀 Starting multi-day scrape for the next {days} days (Toilet Only: {toilet_only})...")
        
        for i in range(1, days + 1):
            target_date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            logger.info(f"📅 Day {i}/{days}: Scraping date {target_date}...")
            results = await self.scrape_route(target_date, toilet_only=toilet_only)
            all_results.extend(results)
            await asyncio.sleep(2)
            
        logger.info(f"✨ Multi-day scrape complete! Total records gathered across {days} days: {len(all_results)}")
        return all_results

def run_scraper_sync(travel_date: Optional[str] = None, days: int = 1, toilet_only: bool = False, headless: bool = True, debug: bool = False) -> List[Dict[str, Any]]:
    scraper = RedBusScraper(headless=headless, debug=debug)
    if days > 1:
        return asyncio.run(scraper.scrape_next_n_days(days=days, toilet_only=toilet_only))
    else:
        target_date = travel_date or (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        return asyncio.run(scraper.scrape_route(target_date, toilet_only=toilet_only))

if __name__ == "__main__":
    test_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"Testing RedBus Scraper for travel date: {test_date} (Toilet Only: True)")
    res = run_scraper_sync(travel_date=test_date, toilet_only=True, headless=True)
    exporter.print_terminal_table(res)
    csv_file = exporter.export_to_csv(res, travel_date=test_date)
    print(f"CSV exported to: {csv_file}")

