# src/briefing/text_blocks_fr.py
"""
French text blocks — same 4-dict structure as text_blocks_de.py.
Slots are identical: {region}, {cdi}, {cdi_label}, {spi_3m:.2f}, etc.
"""
from __future__ import annotations

LAGE_BLOCKS: dict[str, dict[int, str]] = {
    "behoerden": {
        0: "{region} : CDI {cdi} ({cdi_label}). SPI-3m {spi_3m:.2f}. Humidité du sol {soil_moisture_pct:.0f}% RFU. VHI {vhi:.1f}.",
        1: "{region} : CDI {cdi} ({cdi_label}). SPI-3m {spi_3m:.2f}. Humidité du sol {soil_moisture_pct:.0f}% RFU. VHI {vhi:.1f}.",
        2: "{region} : CDI {cdi} ({cdi_label}). SPI-3m {spi_3m:.2f} (sous le seuil -0.84). Humidité du sol {soil_moisture_pct:.0f}% RFU. VHI {vhi:.1f}.",
        3: "{region} : CDI {cdi} ({cdi_label}). SPI-3m {spi_3m:.2f}. Humidité du sol {soil_moisture_pct:.0f}% RFU. VHI {vhi:.1f}. Vigilance accrue requise.",
        4: "{region} : CDI {cdi} ({cdi_label}). SPI-3m {spi_3m:.2f}. Humidité du sol {soil_moisture_pct:.0f}% RFU. VHI {vhi:.1f}. Examiner les mesures immédiates.",
        5: "{region} : CDI {cdi} ({cdi_label}). SPI-3m {spi_3m:.2f}. Humidité du sol {soil_moisture_pct:.0f}% RFU. VHI {vhi:.1f}. Situation extraordinaire.",
    },
    "bulletin": {
        0: "Dans {region}, la situation de sécheresse est normale. L'indice combiné de sécheresse (CDI) est de {cdi} et n'indique aucune sécheresse. L'humidité du sol est de {soil_moisture_pct:.0f}% de la réserve facilement utilisable (RFU).",
        1: "Dans {region}, une légère sécheresse est observée (CDI {cdi}). Les précipitations des trois derniers mois, avec un SPI-3m de {spi_3m:.2f}, sont légèrement inférieures à la moyenne. L'humidité du sol est de {soil_moisture_pct:.0f}% RFU.",
        2: "Dans {region}, une sécheresse notable est constatée (CDI {cdi}). La valeur SPI-3m de {spi_3m:.2f} indique un déficit pluviométrique marqué. L'humidité du sol est de {soil_moisture_pct:.0f}% RFU.",
        3: "Dans {region}, une sécheresse sévère sévit (CDI {cdi}). La valeur SPI-3m de {spi_3m:.2f} indique un déficit pluviométrique important. L'humidité du sol n'est que de {soil_moisture_pct:.0f}% RFU. La situation nécessite une attention particulière.",
        4: "Dans {region}, une sécheresse extrême sévit (CDI {cdi}). La valeur SPI-3m de {spi_3m:.2f} et une humidité du sol de {soil_moisture_pct:.0f}% RFU indiquent une situation très grave. Des mesures pour limiter les dommages doivent être examinées.",
        5: "Dans {region}, une sécheresse exceptionnelle sévit (CDI {cdi}). Il s'agit d'une situation extrême très rare. Toutes les mesures disponibles doivent être examinées.",
    },
}

ENTWICKLUNG_BLOCKS: dict[str, dict[int, str]] = {
    "behoerden": {
        0: "Tendance : {trend_de}. Delta SPI-3m : {spi_3m_delta:+.2f}/semaine. Delta VHI : {vhi_delta:+.1f}.",
        1: "Tendance : {trend_de}. Delta SPI-3m : {spi_3m_delta:+.2f}/semaine. Delta VHI : {vhi_delta:+.1f}.",
        2: "Tendance : {trend_de}. Delta SPI-3m : {spi_3m_delta:+.2f}/semaine. Delta VHI : {vhi_delta:+.1f}.",
        3: "Tendance : {trend_de}. Delta SPI-3m : {spi_3m_delta:+.2f}/semaine. Delta VHI : {vhi_delta:+.1f}. Surveiller l'évolution.",
        4: "Tendance : {trend_de}. Delta SPI-3m : {spi_3m_delta:+.2f}/semaine. Delta VHI : {vhi_delta:+.1f}. Escalade possible.",
        5: "Tendance : {trend_de}. Delta SPI-3m : {spi_3m_delta:+.2f}/semaine. Delta VHI : {vhi_delta:+.1f}. Surveillance critique de la situation.",
    },
    "bulletin": {
        0: "La situation dans {region} est stable. Aucun changement significatif par rapport à la semaine précédente.",
        1: "La situation de sécheresse dans {region} {trend_de_bulletin}. La valeur SPI-3m a évolué de {spi_3m_delta:+.2f}.",
        2: "La situation de sécheresse dans {region} {trend_de_bulletin}. L'état de la végétation (VHI) a évolué de {vhi_delta:+.1f} points.",
        3: "La sécheresse sévère dans {region} {trend_de_bulletin}. Une attention particulière est requise pour l'agriculture et l'approvisionnement en eau.",
        4: "La sécheresse extrême dans {region} {trend_de_bulletin}. Le SPI-3m a évolué de {spi_3m_delta:+.2f}. Des mesures immédiates pourraient être nécessaires.",
        5: "La sécheresse exceptionnelle dans {region} persiste. Toutes les capacités d'intervention disponibles devraient être mobilisées.",
    },
}

EINORDNUNG_BLOCKS: dict[str, dict[int, str]] = {
    "behoerden": {
        0: "Contextualisation hist. : {pct_critical_pct:.0f}% semaines critiques (52 dern. sem.). SPI-3m au {spi_3m_percentile}e percentile (réf. 1961-2020). Aucune anomalie.",
        1: "Contextualisation hist. : {pct_critical_pct:.0f}% semaines critiques (52 dern. sem.). SPI-3m au {spi_3m_percentile}e percentile (réf. 1961-2020).",
        2: "Contextualisation hist. : {pct_critical_pct:.0f}% semaines critiques (52 dern. sem.). SPI-3m au {spi_3m_percentile}e percentile (réf. 1961-2020). Sous la médiane.",
        3: "Contextualisation hist. : {pct_critical_pct:.0f}% semaines critiques (52 dern. sem.). SPI-3m au {spi_3m_percentile}e percentile (réf. 1961-2020). Situation rare.",
        4: "Contextualisation hist. : {pct_critical_pct:.0f}% semaines critiques (52 dern. sem.). SPI-3m au {spi_3m_percentile}e percentile (réf. 1961-2020). Situation extrême très rare.",
        5: "Contextualisation hist. : {pct_critical_pct:.0f}% semaines critiques (52 dern. sem.). SPI-3m au {spi_3m_percentile}e percentile (réf. 1961-2020). Exceptionnellement rare.",
    },
    "bulletin": {
        0: "Par rapport à la moyenne à long terme (1961-2020), la situation actuelle dans {region} est normale. Au cours des 52 dernières semaines, il y a eu {pct_critical_pct:.0f}% de semaines avec une sécheresse critique (CDI >= 3).",
        1: "La valeur SPI-3m se situe au {spi_3m_percentile}e percentile de la période de référence 1961-2020. Au cours des 52 dernières semaines, {pct_critical_pct:.0f}% des semaines étaient critiques.",
        2: "La valeur SPI-3m actuelle se situe au {spi_3m_percentile}e percentile de la période de référence 1961-2020. Au cours des 52 dernières semaines, {pct_critical_pct:.0f}% étaient critiques.",
        3: "La valeur SPI-3m se situe au {spi_3m_percentile}e percentile de la période de référence — une situation rare. Au cours des 52 dernières semaines, il y a eu {pct_critical_pct:.0f}% de semaines critiques.",
        4: "La valeur SPI-3m se situe au {spi_3m_percentile}e percentile de la période de référence — une situation extrême très rare. {pct_critical_pct:.0f}% des 52 dernières semaines étaient critiques.",
        5: "La valeur SPI-3m se situe au {spi_3m_percentile}e percentile de la période de référence — exceptionnellement rare. Dans {pct_critical_pct:.0f}% des 52 dernières semaines, une sécheresse critique régnait.",
    },
}

DATENGRUNDLAGE_BLOCKS: dict[str, str] = {
    "behoerden": (
        "Source : OFEV trockenheit.admin.ch. État des données : {data_timestamp}. "
        "Couverture : {coverage_pct:.0%}. Qualité des données : {overall}. "
        "Incertitudes : les valeurs sont basées sur des calculs de modèles ; des écarts locaux sont possibles."
    ),
    "bulletin": (
        "Les données proviennent de l'Office fédéral de l'environnement (OFEV), "
        "source : trockenheit.admin.ch. État : {data_timestamp}. "
        "Couverture des données : {coverage_pct:.0%}. "
        "Les valeurs sont basées sur des mesures et des calculs de modèles ; des écarts locaux sont possibles."
    ),
}
