# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and
clarifying questions come before implementation rather than after mistakes.

## Test-Driven Development

This project works exclusively in strict test-driven development. You do not write production code without a failing
test proving it's needed first. This is not a style preference — it's the Iron Law you operate under.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

If you catch yourself about to write implementation code before its test exists, stop. Write the test first. If you ever
do write code before its test (e.g. while exploring), delete it — don't keep it "as reference" and don't adapt it while
writing the test afterward. Implement fresh from the test.

**Exceptions** (throwaway prototypes, generated code, config files): ask the user explicitly before skipping TDD for
these. Never decide on your own that "this case is different."

## Project Overview

Warren Bot is a Discord investment club chatbot that analyzes stocks, tracks portfolio performance, and provides
financial reports. The bot integrates with yfinance for market data and generates comprehensive stock analysis reports
including Graham valuation calculations.

## Architecture

### Core Structure

- **src/warren_bot/** - Main application module
    - `__main__.py` - Discord bot entry point and command handling
    - `stock_analysis.py` - Stock analysis and Graham valuation calculations
    - `portfolio_analysis.py` - Club portfolio tracking and reporting
    - `yfinance_integration.py` - Yahoo Finance API integration via yfinance
    - `analysis.py` - Quantitative analysis methods
    - `utilities.py` - General utility functions
    - `logging_config.py` - Centralized logging configuration

### Key Components

- **Discord Integration**: Uses discord.py library with async command handling
- **Financial Data**: yfinance for stock quotes, fundamentals, and historical data
- **Analysis Engine**: Pandas/NumPy for data processing, matplotlib for charting
- **Report Generation**: HTML templates with Jinja2, PDF generation with xhtml2pdf

### Configuration Files

- `.env` - Discord token (use template)
- `club_info.json` - Investment club metadata and settings
- `club_stocks.csv` - Portfolio holdings and transactions

## Development Commands

### Setup and Installation

```bash
# Install dependencies
poetry install

# Activate virtual environment  
poetry shell
```

### Testing

```bash
# Run all tests with coverage
tox

# Run specific Python version tests
tox -e py313

# Run linting only
tox -e flake8

# Run pylint only  
tox -e pylint

# Single test run with pytest
poetry run pytest src/tests/ --cov=src/warren_bot
```

### Code Quality

```bash
# Format code with Black
poetry run black src/

# Run flake8 linting
poetry run flake8 --ignore=E501,D401 src/warren_bot

# Run pylint
poetry run pylint src
```

### Running the Bot

```bash
# Run the Discord bot
poetry run warren_bot

# Or directly with Python
python src/warren_bot/__main__.py
```

### Version Management

```bash
# Bump version (configured with bump-my-version)
bump-my-version patch|minor|major
```

## Bot Commands

The Discord bot responds to these commands:

- `!stock_report <ticker>` or `!sr <ticker>` - Generate comprehensive stock analysis
- `!graham_value <ticker>` - Calculate Graham revised valuation formula
- `!club_report` or `!cr` - Generate club portfolio performance report
- `!terms_of_use` - Display terms of use
- `!help` - Show available commands

## Configuration Requirements

1. **Discord Bot Token**: Create bot at https://discord.com/developers/applications
2. **Club Data**: Configure `club_info.json` and `club_stocks.csv` for portfolio tracking

Note: yfinance does not require an API key, making setup simpler than previous Alpha Vantage integration.

## Code Style Guidelines

- **Line Length**: 120 characters (Black), 120 for flake8
- **Python Version**: 3.13+
- **Linting**: flake8 with docstring requirements, pylint for additional checks
- **Testing**: pytest with coverage reporting
- **Type Hints**: Not consistently used but encouraged for new code

## Key Dependencies

- **discord.py**: Discord bot framework
- **pandas/numpy**: Data analysis and manipulation
- **matplotlib/mplfinance**: Chart generation
- **yfinance**: Financial data retrieval from Yahoo Finance
- **prettytable**: ASCII table formatting
- **jinja2**: HT