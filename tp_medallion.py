import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(16, 9))
ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.axis("off")
ax.set_facecolor("#f8f9fa")
fig.patch.set_facecolor("#f8f9fa")

def boite(ax, x, y, w, h, titre, lignes, couleur_titre, couleur_fond):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                         facecolor=couleur_fond, edgecolor=couleur_titre, linewidth=2)
    ax.add_patch(box)
    ax.text(x + w/2, y + h - 0.35, titre, ha="center", va="center",
            fontsize=10, fontweight="bold", color="white",
            bbox=dict(facecolor=couleur_titre, edgecolor="none", boxstyle="round,pad=0.2", alpha=0.95))
    for i, ligne in enumerate(lignes):
        ax.text(x + 0.2, y + h - 0.8 - i * 0.38, f"• {ligne}",
                ha="left", va="center", fontsize=7.5, color="#333333")

def fleche(ax, x1, y, x2):
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="-|>", color="#555555", lw=2))

#couleurs par couche
C_BRONZE = "#cd7f32"
C_SILVER = "#708090"
C_GOLD   = "#b8860b"
C_BI     = "#2e86ab"

F_BRONZE = "#fff4e6"
F_SILVER = "#f0f0f5"
F_GOLD   = "#fffbe6"
F_BI     = "#e8f4f8"

#BRONZE
boite(ax, 0.3, 1.5, 3.2, 6,
      "BRONZE — Données brutes",
      ["caract-2024.csv", "lieux-2024.csv", "usagers-2024.csv", "vehicules-2024.csv",
       "", "Données brutes telles que", "téléchargées sur data.gouv.fr",
       "", "Aucune transformation", "Format original (CSV, sep=';')",
       "Encodage latin1"],
      C_BRONZE, F_BRONZE)

fleche(ax, 3.5, 4.5, 4.3)

#SILVER
boite(ax, 4.3, 1.5, 3.2, 6,
      "SILVER — Données nettoyées",
      ["silver_caract.csv", "silver_lieux.csv", "silver_usagers.csv", "silver_vehicules.csv",
       "", "Colonnes vides supprimées", "Doublons supprimés",
       "Coords GPS converties", "DOM-TOM mis de côté",
       "Colonnes enrichies :", "  date, tranche_horaire,", "  gravite_max"],
      C_SILVER, F_SILVER)

fleche(ax, 7.5, 4.5, 8.3)

#GOLD
boite(ax, 8.3, 1.5, 3.2, 6,
      "GOLD — Modèle analytique",
      ["gold_fait_accidents.csv", "gold_dim_lieu.csv", "gold_dim_vehicule.csv", "gold_dim_usager.csv",
       "", "Modèle en étoile", "Fait : 51 063 accidents",
       "Clé de jointure : Num_Acc",
       "", "Prêt pour l'analyse", "et la visualisation"],
      C_GOLD, F_GOLD)

fleche(ax, 11.5, 4.5, 12.3)

#BI
boite(ax, 12.3, 1.5, 3.2, 6,
      "BI / Dashboards",
      ["", "Analyses possibles :", "",
       "Accidents par dept", "Gravité par heure", "Type de route vs gravité",
       "Météo vs accidents", "Évolution temporelle",
       "", "Outils : Power BI,", "Tableau, Python"],
      C_BI, F_BI)

#titre
ax.text(8, 8.5, "Architecture Medallion — Accidents Routiers France 2024",
        ha="center", va="center", fontsize=14, fontweight="bold", color="#222222")

plt.tight_layout()
plt.savefig("medallion_architecture.png", dpi=150, bbox_inches="tight")
print("[OK] diagramme sauvegardé : medallion_architecture.png")
plt.show()
