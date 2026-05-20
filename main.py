import sys

from src.validator import validate_ticker
from src.fetcher import fetch_basics
from src.formatter import display_basics


def run_analysis(ticker: str) -> None:
    try:
        info = validate_ticker(ticker)
        data = fetch_basics(info)
        display_basics(data)
    except Exception as e:
        print(f"❌ {e}")


def in_jupyter() -> bool:
    return "ipykernel" in sys.modules


def main_jupyter() -> None:
    import ipywidgets as widgets
    from IPython.display import display, clear_output

    ticker_input = widgets.Text(placeholder="Ex: TEM", description="Ticker:")
    run_button = widgets.Button(description="Run", button_style="primary")
    output = widgets.Output()

    def on_run(_):
        with output:
            clear_output()
            run_analysis(ticker_input.value)

    run_button.on_click(on_run)
    display(ticker_input, run_button, output)


def main_cli() -> None:
    ticker = sys.argv[1] if len(sys.argv) > 1 else input("Ticker : ")
    run_analysis(ticker)


if in_jupyter():
    main_jupyter()
elif __name__ == "__main__":
    main_cli()