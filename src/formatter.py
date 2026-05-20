def display_basics(data: dict) -> None:
    print(f"Entreprise : {data['name']} ({data['ticker']})")
    print(f"Prix       : {data['price']} {data['currency']}")