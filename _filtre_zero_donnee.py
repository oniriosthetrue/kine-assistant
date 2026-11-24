"""
Filtre de securite "Zero donnee patient" pour l'Assistant Kine.

Evenement `outlet` : s'execute APRES la reponse du modele, AVANT affichage.
Il remplace toute valeur concrete identifiant un patient (nom, age, date,
EVA, score, amplitude, nb de seances) par le marqueur [A COMPLETER],
tout en PRESERVANT les vrais champs [ ... ] deja presents dans la trame.

C'est la ceinture de securite : meme si le modele invente une donnee,
elle n'atteint jamais l'ecran du praticien.

NB : le handler doit etre une FONCTION DE MODULE nommee `outlet`
(Open WebUI fait getattr(module, 'outlet')), pas une methode de classe.
"""

import re


# --- Motifs "surs" : quasi exclusivement des donnees patient, jamais un
#     referentiel public. Grattes dans TOUS les cas (question ou courrier). ---
_SAFE_PATTERNS = [
    # Nom apres une civilite / titre.
    (r"\b(?:M\.|Mme|Monsieur|Madame|Dr\.?|Docteur|Pr\.?|Professeur)\s+"
     r"[A-ZÀ-Ý][\w'’À-ÿ\-]+(?:\s+[A-ZÀ-Ý][\w'’À-ÿ\-]+)?", None),
    # Valeur d'une etiquette "Nom"/"Prenom" (cellule de tableau ou en ligne).
    (r"(?i)(\|\s*\**\s*(?:nom de famille|pr[ée]nom|nom)\s*\**\s*\|\s*)([^|\n]+?)(\s*\|)",
     r"\1[A COMPLETER]\3"),
    (r"(?i)(\b(?:nom de famille|pr[ée]nom|nom)\b[ \t]*:[ \t]*)([^\n|]+)",
     r"\1[A COMPLETER]"),
    # Score / EVA sur echelle (/10, /100, /5). Le lookahead (?!\s*/) evite de
    # hacher un fragment de date (ex "05/10" dans "05/10/2026").
    (r"\b\d{1,3}\s*/\s*(?:10|100|5)\b(?!\s*/)", None),
    # Taille au format "1m75".
    (r"\b\d{1,2}m\d{2}\b", None),
    # Age : jamais une valeur de referentiel dans ce corpus -> toujours gratte.
    (r"(?i)\b\d{1,3}\s*ans?\b", None),
]

# --- Motifs "ambigus" : peuvent designer AUSSI une donnee de referentiel
#     (taux en %, tarif dans un tableau, "8 seances" d'acces direct, date
#     officielle d'un texte). Grattes UNIQUEMENT en mode agressif, c.-a-d.
#     quand le message de l'utilisateur contient une donnee patient
#     (= redaction de courrier / CR). En question de gestion, on les laisse. ---
_AMBIGUOUS_PATTERNS = [
    # Dates jj/mm/aaaa puis jj/mm (AVANT le score NN/MM, sinon "12/03" serait
    # hache par le score et laisserait "/2026" apparent).
    (r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", None),
    (r"\b\d{1,2}/\d{1,2}\b", None),
    # Date en toutes lettres "12 mars 2026" / "12 mars" : le modele reecrit
    # parfois la date du courrier en lettres, que les motifs numeriques ne
    # verraient pas. En mode agressif (courrier), toute date = donnee patient.
    (r"(?i)\b\d{1,2}\s+(?:janvier|f[ée]vrier|mars|avril|mai|juin|juillet|ao[ûu]t|"
     r"septembre|octobre|novembre|d[ée]cembre)\b(?:\s*\d{2,4})?", None),
    # Score sur une echelle quelconque "NN/MM" (PCS 28/52, Tampa 41/43). Motif
    # ambigu : pertinent seulement en contexte patient (courrier/CR).
    (r"\b\d{1,3}\s*/\s*\d{1,3}\b", None),
    # Nombre de seances (clinique) : "24 seances", "Séance n°3", "Séances 1 à 8".
    (r"(?i)\b\d{1,3}\s*s[ée]ances?\b", None),
    (r"(?i)\bs[ée]ance\s*n[°ºo]?\s*\d+", None),
    (r"(?i)(\bs[ée]ances?\s+)(?:\d+\s*[àa\-–~]\s*\d+|\d+)", r"\g<1>[A COMPLETER]"),
    # Nombre + unite (cm, mm, kg, degres, %).
    (r"(?i)\b\d{1,3}(?:[.,]\d+)?\s*(?:cm|mm|kg|°|degr[ée]s|%)", None),
    # Valeur isolee apres un libelle de donnee patient (ex "seances : 18").
    (r"(?i)(\b(?:seances?|s[ée]ances?|age|poids|taille|tension|fr[ée]quence|rythme|nombre)\b"
     r"[ \t]*:?[ \t]*)(\d+(?:[.,]\d+)?)", r"\1[A COMPLETER]"),
]

# Cellule(s) numerique(s) d'une ligne de tableau (traitee a part, en agressif).
_TABLE_ROW_RE = re.compile(r"(?m)^.*\|.*$")


def _apply(text, patterns):
    for pat, repl in patterns:
        text = re.sub(pat, repl if repl is not None else "[A COMPLETER]", text)
    return text


def _scrub(text: str, aggressive: bool = True) -> str:
    """Masque les donnees patient. aggressive=True (redaction de courrier) :
    gratte aussi les motifs ambigus (% , dates, seances, tableaux).
    aggressive=False (question de gestion) : ne gratte que les motifs surs,
    afin de laisser apparaitre les chiffres du referentiel (taux, tarifs...)."""
    # 1. Proteger les vrais champs [ ... ] (ne jamais les toucher).
    protected = []

    def _protect(m):
        protected.append(m.group(0))
        return "\u0000{}\u0000".format(len(protected) - 1)

    text = re.sub(r"\[[^\[\]]*\]", _protect, text)

    # 2. Motifs surs (toujours).
    text = _apply(text, _SAFE_PATTERNS)

    # 3. Motifs ambigus (mode agressif seulement).
    if aggressive:
        text = _apply(text, _AMBIGUOUS_PATTERNS)
        # Ligne de tableau de bilan : toute cellule numerique.
        text = _TABLE_ROW_RE.sub(
            lambda m: re.sub(r"\d+(?:[.,]\d+)?", "[A COMPLETER]", m.group(0))
            if "|" in m.group(0) and not m.group(0).lstrip().startswith("|--")
            and not set(m.group(0).strip()) <= set("|-: ")
            else m.group(0),
            text,
        )

    # 4. Restaurer les champs proteges.
    def _restore(m):
        return protected[int(m.group(1))]

    text = re.sub(r"\u0000(\d+)\u0000", _restore, text)
    return text


# Signaux UNIVOQUEMENT patients dans le message UTILISATEUR. On n'y met PAS
# les dates ni les ages : une question de gestion cite souvent une date
# officielle ("loi du 19/05/2023") ou un age de referentiel ("a partir de 65
# ans"), ce qui declencherait a tort le mode agressif et re-masquerait les
# chiffres. L'age reste couvert par les motifs surs (toujours grattes) ; la
# date, elle, n'est pas identifiante sans nom.
_PATIENT_DATA_RE = re.compile(
    r"(?:"
    r"\b(?:M\.|Mme|Monsieur|Madame|Dr\.?|Docteur|Pr\.?|Professeur)\s+[A-ZÀ-Ý]"
    r"|\b\d{1,3}\s*/\s*(?:10|100|5)\b(?!\s*/)"  # EVA / score clinique (pas une date)
    r"|\b\d{1,2}m\d{2}\b"                     # taille
    r"|\b(?:nom|pr[ée]nom)\b[ \t]*:"          # etiquette
    r")",
    re.IGNORECASE,
)


def _has_patient_data(messages) -> bool:
    """Le mode agressif se declenche sur la DERNIERE question de l'utilisateur
    uniquement : un suivi du type « et le taux de remboursement ? » ne doit pas
    rester en mode courrier a cause d'un nom cite plus haut dans le fil. (Le
    nom reste de toute facon toujours masque, c'est un motif sur.)"""
    for message in reversed(messages):
        if message.get("role") != "user":
            continue
        content = message.get("content")
        if isinstance(content, str):
            return bool(_PATIENT_DATA_RE.search(content))
        return False
    return False


def _scrub_output(output, aggressive: bool = True):
    """Le frontend re-rend a partir du champ `output` (liste d'items, chacun
    avec content[].text). On doit gratter ces textes imbriques, sinon la
    donnee inventee reapparait a l'ecran meme si `content` est propre."""
    import json

    was_str = isinstance(output, str)
    if was_str:
        try:
            data = json.loads(output)
        except Exception:
            return _scrub(output, aggressive)
    else:
        data = output

    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            # Le "reasoning" (chaine de pensee du modele) recopie souvent le
            # prompt mot a mot, y compris les noms de patient en texte libre
            # qu'aucune regex ne rattrape. Ce n'est pas la livrable clinique :
            # on le vide entierement.
            if item.get("type") == "reasoning":
                content = item.get("content")
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and "text" in part:
                            part["text"] = ""
                elif isinstance(content, str):
                    item["content"] = ""
                summary = item.get("summary")
                if isinstance(summary, list):
                    for part in summary:
                        if isinstance(part, dict) and "text" in part:
                            part["text"] = ""
                elif isinstance(summary, str):
                    item["summary"] = ""
                continue
            content = item.get("content")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and isinstance(part.get("text"), str):
                        part["text"] = _scrub(part["text"], aggressive)
            elif isinstance(content, str):
                item["content"] = _scrub(content, aggressive)
    elif isinstance(data, dict):
        content = data.get("content")
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    part["text"] = _scrub(part["text"], aggressive)
        elif isinstance(content, str):
            data["content"] = _scrub(content, aggressive)

    if was_str:
        return json.dumps(data)
    return data


class Filter:
    async def outlet(self, body: dict, __user__=None, __metadata__=None, __event_emitter__=None):
        try:
            messages = body.get("messages") or []
            # Mode agressif (masquage complet) UNIQUEMENT si l'utilisateur a
            # fourni une donnee patient (= redaction de courrier / CR). Pour
            # une question de gestion, on laisse les chiffres du referentiel.
            aggressive = _has_patient_data(messages)
            for message in messages:
                if message.get("role") != "assistant":
                    continue
                content = message.get("content")
                if isinstance(content, str) and content:
                    message["content"] = _scrub(content, aggressive)
                output = message.get("output")
                if output:
                    message["output"] = _scrub_output(output, aggressive)
        except Exception:
            pass
        return body
