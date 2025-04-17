class BaseSerializzazione:
    """
    Classe con funzionalità di serializzazione per gli stati base.
    Contiene metodi per convertire gli stati in dizionari e viceversa.
    """
    
    @staticmethod
    def to_dict(state):
        """
        Converte lo stato in un dizionario per la serializzazione.
        Salva automaticamente gli attributi base e permette l'estensione nelle sottoclassi.
        
        Args:
            state: L'istanza dello stato da serializzare
            
        Returns:
            dict: Rappresentazione dello stato in formato dizionario
        """
        # Salva il tipo dello stato per la ricostruzione
        data = {
            "type": state.__class__.__name__
        }
        
        # Aggiungi automaticamente tutti gli attributi serializzabili
        for attr_name, attr_value in state.__dict__.items():
            # Ignora attributi privati o funzioni
            if attr_name.startswith('_') or callable(attr_value):
                continue
                
            # Gestisci tipi base serializzabili
            if isinstance(attr_value, (str, int, float, bool, type(None))):
                data[attr_name] = attr_value
            # Gestisci oggetti con to_dict()
            elif hasattr(attr_value, 'to_dict') and callable(getattr(attr_value, 'to_dict')):
                try:
                    data[attr_name] = attr_value.to_dict()
                except:
                    # Se il to_dict() fallisce, ignora questo attributo
                    pass
            # Gestisci liste di oggetti
            elif isinstance(attr_value, list):
                serialized_list = []
                try:
                    for item in attr_value:
                        if hasattr(item, 'to_dict') and callable(getattr(item, 'to_dict')):
                            serialized_list.append(item.to_dict())
                        elif isinstance(item, (str, int, float, bool, type(None))):
                            serialized_list.append(item)
                        # Ignora gli elementi che non possono essere serializzati
                    if serialized_list:  # Aggiungi solo se la lista non è vuota
                        data[attr_name] = serialized_list
                except:
                    # Se c'è un errore di serializzazione, ignora questo attributo
                    pass
            # Gestisci dizionari di oggetti
            elif isinstance(attr_value, dict):
                serialized_dict = {}
                try:
                    for key, value in attr_value.items():
                        # Converti la chiave a stringa per assicurare compatibilità JSON
                        str_key = str(key)
                        if hasattr(value, 'to_dict') and callable(getattr(value, 'to_dict')):
                            serialized_dict[str_key] = value.to_dict()
                        elif isinstance(value, (str, int, float, bool, type(None))):
                            serialized_dict[str_key] = value
                        # Ignora i valori che non possono essere serializzati
                    if serialized_dict:  # Aggiungi solo se il dict non è vuoto
                        data[attr_name] = serialized_dict
                except:
                    # Se c'è un errore di serializzazione, ignora questo attributo
                    pass
            # Gestisci tuple (convertendole in liste)
            elif isinstance(attr_value, tuple):
                try:
                    data[attr_name] = list(attr_value)
                except:
                    pass
        
        return data
        
    @staticmethod
    def from_dict(cls, data):
        """
        Crea un'istanza di stato da un dizionario.
        
        Args:
            cls: La classe di stato da istanziare
            data (dict): Dizionario con i dati dello stato
            
        Returns:
            BaseState: Nuova istanza di stato o istanza di base in caso di errore
        """
        # Se c'è un tipo specifico, crea l'istanza appropriata
        state_type = data.get("type")
        if state_type != cls.__name__:
            # Importazione dinamica dello stato corretto
            import importlib
            import traceback
            
            try:
                # Cerca in tutti i moduli states
                # Correzione: mappatura esplicita dei nomi delle classi ai moduli
                state_module_map = {
                    "TavernaState": "taverna",
                    "MercatoState": "mercato",
                    "CombattimentoState": "combattimento",
                    "DialogoState": "dialogo",
                    "GestioneInventarioState": "gestione_inventario",
                    "ProvaAbilitaState": "prova_abilita",
                    "MappaState": "mappa_state",
                    "SceltaMappaState": "scelta_mappa_state",
                    "MenuState": "menu"
                }
                
                # Usa la mappatura se disponibile, altrimenti fallback al nome in minuscolo
                module_suffix = state_module_map.get(state_type, state_type.lower())
                module_name = f"states.{module_suffix}"
                
                module = importlib.import_module(module_name)
                state_class = getattr(module, state_type)
                
                # Crea l'istanza usando il metodo from_dict della classe
                if hasattr(state_class, 'from_dict'):
                    return state_class.from_dict(data)
                else:
                    # Se non ha un metodo from_dict, crea un'istanza di default
                    return state_class()
            except (ImportError, AttributeError) as e:
                # Log dell'errore per debug
                print(f"Errore durante il caricamento dello stato {state_type}: {e}")
                print(traceback.format_exc())
                # Fallback a un'istanza base invece di None
                return cls()
            except Exception as e:
                # Cattura qualsiasi altro errore imprevisto
                print(f"Errore imprevisto durante il caricamento dello stato: {e}")
                print(traceback.format_exc())
                return cls()
        
        # Istanza base
        return cls() 