"""
Professional Web Shell Scanner - PYDROID3 EDITION
Version: 2.0 | Author: Security Researcher
"""

import asyncio
import aiohttp
import aiofiles
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Set
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from colorama import init, Fore, Style
import signal
import sys

# Initialize colorama
init(autoreset=True)

class WebShellScanner:
    """Professional Web Shell Scanner"""
    
    def __init__(self, output_file: str = "shelly.txt"):
        self.output_file = Path(output_file)
        self.session = None
        self.paths = []
        self.results = set()
        self.setup_logging()
        self.load_paths()
        
    def setup_logging(self):
        """Configure logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def load_paths(self):
        """Load paths from List.txt"""
        try:
            with open("List.txt", "r", encoding="utf-8") as file:
                self.paths = [p.strip() for p in file.read().splitlines() if p.strip()]
            print(f"{Fore.CYAN}[*] Loaded {len(self.paths)} paths{Style.RESET_ALL}")
        except FileNotFoundError:
            print(f"{Fore.RED}[!] List.txt not found!{Style.RESET_ALL}")
            sys.exit(1)
    
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=15)
        self.session = aiohttp.ClientSession(timeout=timeout, headers=self.get_headers())
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @staticmethod
    def get_headers():
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    @staticmethod
    def get_bot_headers():
        return {
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        }
    
    def get_today_dates(self):
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        return today.strftime("%d/%m/%Y"), tomorrow.strftime("%d/%m/%Y")
    
    def is_valid_domain(self, domain: str) -> bool:
        return not domain.endswith(".tr") and domain.strip()
    
    def print_banner(self):
        print(f"""
{Fore.GREEN}{Style.BRIGHT}
╔══════════════════════════════════════╗
║    PROFESSIONAL WEB SHELL SCANNER    ║
║              Version 2.0             ║
║           PYDROID3 EDITION           ║
╚══════════════════════════════════════╝{Style.RESET_ALL}
        """)
    
    async def fetch_today_domains(self, base_url: str) -> List[str]:
        sites = []
        page = 1
        today, tomorrow = self.get_today_dates()
        
        print(f"{Fore.CYAN}[*] Fetching from: {base_url}{Style.RESET_ALL}")
        
        while True:
            try:
                async with self.session.get(
                    urljoin(base_url, str(page)), 
                    headers=self.get_bot_headers()
                ) as response:
                    if response.status != 200:
                        break
                        
                    text = await response.text()
                    soup = BeautifulSoup(text, "html.parser")
                    rows = soup.select("tbody tr")
                    
                    if not rows:
                        break
                        
                    found_today = False
                    
                    for row in rows:
                        try:
                            cells = row.find_all("td")
                            if len(cells) < 9:
                                continue
                                
                            date = cells[0].get_text(strip=True)
                            domain = cells[8].get_text(strip=True)
                            
                            if date not in (today, tomorrow):
                                continue
                                
                            found_today = True
                            domain = domain.split("/")[0].strip()
                            
                            if self.is_valid_domain(domain):
                                sites.append(f"http://{domain}/")
                                
                        except:
                            continue
                    
                    if not found_today:
                        break
                        
                    page += 1
                    
            except:
                break
        
        return sites
    
    async def check_single_url(self, url: str, path: str) -> bool:
        full_url = urljoin(url, path)
        try:
            async with self.session.get(full_url) as response:
                if response.status != 200:
                    return False
                    
                text = await response.text()
                shell_indicators = [
                    'type="file"',
                    'name="command"',
                    '<pre align=center><form method=post>Password<br>',
                    '<input type=password name=pass'
                ]
                
                for indicator in shell_indicators:
                    if indicator in text:
                        print(f"{Fore.GREEN}[+] SHELL FOUND: {Fore.WHITE}{full_url}{Style.RESET_ALL}")
                        self.results.add(full_url)
                        return True
                        
        except:
            pass
        
        print(f"{Fore.RED}[-] Clean: {Fore.WHITE}{full_url[:40]}...{Style.RESET_ALL}")
        return False
    
    async def scan_site(self, url: str):
        for path in self.paths:
            if await self.check_single_url(url, path):
                break
    
    async def scan_url_list(self, url_list: List[str]):
        semaphore = asyncio.Semaphore(20)  # Pydroid3 için azaltıldı
        
        async def limited_scan(url):
            async with semaphore:
                await self.scan_site(url)
        
        tasks = [limited_scan(url) for url in url_list]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def save_results(self):
        if self.results:
            async with aiofiles.open(self.output_file, "w", encoding="utf-8") as f:
                for result in sorted(self.results):
                    await f.write(result + "\n")
            print(f"{Fore.GREEN}[+] SAVED {len(self.results)} shells to {self.output_file}{Style.RESET_ALL}")

def signal_handler(signum, frame):
    print(f"\n{Fore.YELLOW}[!] Scan stopped!{Style.RESET_ALL}")
    sys.exit(0)

def parse_args():
    parser = argparse.ArgumentParser(description="Web Shell Scanner")
    parser.add_argument("-u", "--url", help="Single URL")
    parser.add_argument("-f", "--file", help="URL file")
    parser.add_argument("-t", "--today", action="store_true", help="Today's hacks")
    parser.add_argument("-o", "--output", default="shelly.txt", help="Output file")
    return parser.parse_args()

async def main():
    args = parse_args()
    signal.signal(signal.SIGINT, signal_handler)
    
    scanner = WebShellScanner(args.output)
    scanner.print_banner()
    
    if not (args.url or args.file or args.today):
        print(f"{Fore.YELLOW}Use: python scanner.py -t | -u URL | -f file.txt{Style.RESET_ALL}")
        return
    
    async with scanner:
        if args.url:
            await scanner.scan_site(args.url)
            
        elif args.file:
            with open(args.file, "r") as f:
                urls = [line.strip() for line in f if line.strip()]
            print(f"{Fore.CYAN}[*] Scanning {len(urls)} URLs{Style.RESET_ALL}")
            await scanner.scan_url_list(urls)
            
        elif args.today:
            print(f"{Fore.CYAN}[*] Fetching today's hacked sites...{Style.RESET_ALL}")
            sites = []
            defacer_urls = [
                "https://defacer.id/archive/",
                "https://defacer.id/archive/special/",
                "https://defacer.id/archive/onhold/"
            ]
            
            for base_url in defacer_urls:
                sites.extend(await scanner.fetch_today_domains(base_url))
            
            sites = list(set(sites))
            print(f"{Fore.GREEN}[+] Found {len(sites)} sites{Style.RESET_ALL}")
            
            if input(f"{Fore.WHITE}[?] Scan shells? (y/n): ").lower() == 'n':
                await scanner.save_results()
                return
            
            await scanner.scan_url_list(sites)
        
        await scanner.save_results()

if __name__ == "__main__":
    asyncio.run(main())