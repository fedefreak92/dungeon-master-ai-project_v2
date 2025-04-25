"""
File di compatibilità per mantenere la retrocompatibilità con il codice esistente.
Questo file importa la classe ProvaAbilitaState dal nuovo package modulare.
"""

from states.prova_abilita import ProvaAbilitaState

# Questo file esiste solo per mantenere la retrocompatibilità
# Tutti i riferimenti dovrebbero essere aggiornati per utilizzare:
#   from states.prova_abilita import ProvaAbilitaState 