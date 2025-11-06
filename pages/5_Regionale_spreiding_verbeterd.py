# -----------------------------------------------------------
# 💶 Gebruikerskosten extractie en aanvulling met mediaan
# -----------------------------------------------------------

def extract_cost(text):
    """Haalt numerieke waarde uit UsageCost-veld, in euro’s/kWh."""
    if pd.isna(text):
        return np.nan
    text = str(text).lower().replace(",", ".")
    match = re.search(r"€\s*([\d.]+)", text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return np.nan
    match_fallback = re.search(r"(\d+\.\d+|\d+)", text)
    if match_fallback:
        try:
            value = float(match_fallback.group(1))
            if "ct" in text and value > 1:
                value = value / 100
            return value
        except ValueError:
            return np.nan
    return np.nan

# Kosten parsen
data["ParsedCost"] = data["UsageCost"].apply(extract_cost)

# Mediaan berekenen op bekende waarden
mediaan = data["ParsedCost"].median()

# Opvullen: als onbekend of nul → vervang door mediaan
data["FinalCost"] = data["ParsedCost"].apply(
    lambda x: mediaan if pd.isna(x) or x == 0 else x
)

# Categorieën toekennen
def cost_category(cost, original_text):
    if pd.isna(original_text) or original_text.strip() == "":
        return "Niet bekend"
    elif cost < 0.30:
        return "Goedkoop"
    elif cost < 0.40:
        return "Duur"
    else:
        return "Zeer duur"

data["CostCategory"] = data.apply(
    lambda row: cost_category(row["FinalCost"], row["UsageCost"]), axis=1
)

# Kleurcodering
kleur_mapping = {
    "Niet bekend": "grey",
    "Goedkoop": "lightgreen",
    "Duur": "orange",
    "Zeer duur": "red"
}

data["Color"] = data["CostCategory"].map(kleur_mapping)
