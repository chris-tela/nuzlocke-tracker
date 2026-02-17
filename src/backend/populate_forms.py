"""Populate ``all_pokemon_forms`` from ``all_pokemon.forms`` values.
   Assumption: all_pokemon is populated, all_pokemon_forms is empty
"""

from sqlalchemy.orm import Session

from db import database, models


def populate_forms(db: Session) -> int:
    """Populate forms assuming source data exists and target table is empty."""
    all_pokemon = db.query(models.AllPokemon).all()

    inserted = 0
    inserted = 0

    for pokemon in all_pokemon:
        forms = pokemon.forms or []
        for form_name in forms:
            pokemon_form = models.AllPokemonForms(
                form_name=form_name,
                pokemon_id=pokemon.poke_id,
            )
            db.add(pokemon_form)
            inserted += 1

    db.commit()
    return inserted


def main() -> None:
    # Ensure tables exist before trying to insert any form records.
    models.Base.metadata.create_all(bind=database.engine)

    db = database.SessionLocal()
    try:
        inserted = populate_forms(db)
        print(f"Populate complete. Inserted: {inserted}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
