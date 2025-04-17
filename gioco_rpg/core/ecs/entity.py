import uuid
from typing import Dict, Set, Any, Optional, List

class Entity:
    """
    Rappresenta un'entità nel sistema ECS.
    Un'entità è essenzialmente un contenitore di componenti con un identificatore unico.
    """
    
    def __init__(self, id: str = None, name: str = None):
        """
        Inizializza una nuova entità
        
        Args:
            id: Identificatore univoco dell'entità (opzionale, generato automaticamente se non fornito)
            name: Nome descrittivo dell'entità (opzionale)
        """
        self.id = id or str(uuid.uuid4())
        self.name = name or f"Entity-{self.id[:8]}"
        self.components: Dict[str, Any] = {}  # Componenti indicizzati per tipo
        self.tags: Set[str] = set()  # Tag associati all'entità
        self.active = True  # Indica se l'entità è attiva
        self.marked_for_removal = False  # Indica se l'entità è marcata per la rimozione
        self.abilita: Dict[str, int] = {}  # Abilità dell'entità e relativi valori
        
    def add_component(self, component_type: str, component: Any) -> 'Entity':
        """
        Aggiunge un componente all'entità
        
        Args:
            component_type: Tipo di componente
            component: Istanza del componente
            
        Returns:
            Entity: L'entità stessa (per permettere chiamate a catena)
        """
        self.components[component_type] = component
        return self
        
    def remove_component(self, component_type: str) -> bool:
        """
        Rimuove un componente dall'entità
        
        Args:
            component_type: Tipo di componente da rimuovere
            
        Returns:
            bool: True se il componente è stato rimosso, False se non esisteva
        """
        if component_type in self.components:
            del self.components[component_type]
            return True
        return False
        
    def get_component(self, component_type: str) -> Optional[Any]:
        """
        Recupera un componente dell'entità
        
        Args:
            component_type: Tipo di componente da recuperare
            
        Returns:
            Optional[Any]: Il componente richiesto, o None se non esiste
        """
        return self.components.get(component_type)
        
    def has_component(self, component_type: str) -> bool:
        """
        Verifica se l'entità ha un determinato componente
        
        Args:
            component_type: Tipo di componente da verificare
            
        Returns:
            bool: True se l'entità ha il componente, False altrimenti
        """
        return component_type in self.components
        
    def has_components(self, component_types: List[str]) -> bool:
        """
        Verifica se l'entità ha tutti i componenti specificati
        
        Args:
            component_types: Lista di tipi di componenti da verificare
            
        Returns:
            bool: True se l'entità ha tutti i componenti, False altrimenti
        """
        return all(self.has_component(ctype) for ctype in component_types)
        
    def has_any_component(self, component_types: List[str]) -> bool:
        """
        Verifica se l'entità ha almeno uno dei componenti specificati
        
        Args:
            component_types: Lista di tipi di componenti da verificare
            
        Returns:
            bool: True se l'entità ha almeno uno dei componenti, False altrimenti
        """
        return any(self.has_component(ctype) for ctype in component_types)
        
    def add_tag(self, tag: str) -> 'Entity':
        """
        Aggiunge un tag all'entità
        
        Args:
            tag: Tag da aggiungere
            
        Returns:
            Entity: L'entità stessa (per permettere chiamate a catena)
        """
        self.tags.add(tag)
        return self
        
    def remove_tag(self, tag: str) -> bool:
        """
        Rimuove un tag dall'entità
        
        Args:
            tag: Tag da rimuovere
            
        Returns:
            bool: True se il tag è stato rimosso, False se non esisteva
        """
        if tag in self.tags:
            self.tags.remove(tag)
            return True
        return False
        
    def has_tag(self, tag: str) -> bool:
        """
        Verifica se l'entità ha un determinato tag
        
        Args:
            tag: Tag da verificare
            
        Returns:
            bool: True se l'entità ha il tag, False altrimenti
        """
        return tag in self.tags
        
    def has_any_tag(self, tags: List[str]) -> bool:
        """
        Verifica se l'entità ha almeno uno dei tag specificati
        
        Args:
            tags: Lista di tag da verificare
            
        Returns:
            bool: True se l'entità ha almeno uno dei tag, False altrimenti
        """
        return any(tag in self.tags for tag in tags)
        
    def has_all_tags(self, tags: List[str]) -> bool:
        """
        Verifica se l'entità ha tutti i tag specificati
        
        Args:
            tags: Lista di tag da verificare
            
        Returns:
            bool: True se l'entità ha tutti i tag, False altrimenti
        """
        return all(tag in self.tags for tag in tags)
        
    def deactivate(self) -> None:
        """Disattiva l'entità"""
        self.active = False
        
    def activate(self) -> None:
        """Attiva l'entità"""
        self.active = True
        
    def is_active(self) -> bool:
        """
        Verifica se l'entità è attiva
        
        Returns:
            bool: True se l'entità è attiva, False altrimenti
        """
        return self.active
        
    def mark_for_removal(self) -> None:
        """Marca l'entità per la rimozione"""
        self.marked_for_removal = True
        
    def is_marked_for_removal(self) -> bool:
        """
        Verifica se l'entità è marcata per la rimozione
        
        Returns:
            bool: True se l'entità è marcata per la rimozione, False altrimenti
        """
        return self.marked_for_removal
        
    def get_all_components(self) -> List[Any]:
        """
        Recupera tutti i componenti dell'entità
        
        Returns:
            List[Any]: Lista di tutti i componenti
        """
        return list(self.components.values())

    def get_abilita(self) -> Dict[str, int]:
        """
        Recupera tutte le abilità dell'entità
        
        Returns:
            Dict[str, int]: Dizionario contenente abilità e relativi valori
        """
        # Prima controlla se l'entità ha un attributo abilita
        if self.abilita:
            return self.abilita.copy()
            
        # Altrimenti cerca componenti con abilità
        risultato = {}
        
        # Controlla se c'è un componente di tipo "abilities"
        abilities_comp = self.get_component("abilities")
        if abilities_comp and hasattr(abilities_comp, "abilita"):
            risultato.update(abilities_comp.abilita)
            
        # Cerca anche in altri componenti che potrebbero avere abilità
        for comp in self.components.values():
            if hasattr(comp, "abilita") and isinstance(comp.abilita, dict):
                risultato.update(comp.abilita)
                
        return risultato
        
    def get_bonus_abilita(self, nome_abilita: str) -> int:
        """
        Ottiene il bonus per una specifica abilità
        
        Args:
            nome_abilita: Nome dell'abilità
            
        Returns:
            int: Valore del bonus per l'abilità
        """
        # Controlla prima nella map di abilità dell'entità
        bonus = self.abilita.get(nome_abilita, 0)
        
        # Controlla nei componenti
        for comp in self.components.values():
            # Se il componente ha un metodo get_bonus_abilita
            if hasattr(comp, "get_bonus_abilita") and callable(getattr(comp, "get_bonus_abilita")):
                bonus += comp.get_bonus_abilita(nome_abilita)
                
            # Alternativa: se il componente ha un dizionario di abilità
            elif hasattr(comp, "abilita") and isinstance(comp.abilita, dict):
                bonus += comp.abilita.get(nome_abilita, 0)
                
        return bonus
        
    def aggiungi_abilita(self, nome_abilita: str, valore: int = 0) -> None:
        """
        Aggiunge o aggiorna un'abilità dell'entità
        
        Args:
            nome_abilita: Nome dell'abilità
            valore: Valore dell'abilità
        """
        self.abilita[nome_abilita] = valore
        
    def rimuovi_abilita(self, nome_abilita: str) -> bool:
        """
        Rimuove un'abilità dell'entità
        
        Args:
            nome_abilita: Nome dell'abilità da rimuovere
            
        Returns:
            bool: True se l'abilità è stata rimossa, False se non esisteva
        """
        if nome_abilita in self.abilita:
            del self.abilita[nome_abilita]
            return True
        return False
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Serializza l'entità in un dizionario
        
        Returns:
            Dict[str, Any]: Dizionario rappresentante l'entità
        """
        # Serializza componenti
        components_data = {}
        for comp_type, component in self.components.items():
            if hasattr(component, "to_dict") and callable(getattr(component, "to_dict")):
                components_data[comp_type] = component.to_dict()
            else:
                # Fallback per componenti senza metodo to_dict
                components_data[comp_type] = {"_type": comp_type}
                
        return {
            "id": self.id,
            "name": self.name,
            "components": components_data,
            "tags": list(self.tags),
            "active": self.active,
            "marked_for_removal": self.marked_for_removal,
            "abilita": self.abilita.copy()
        }
        
    serialize = to_dict  # Alias per compatibilità
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """
        Crea un'entità da un dizionario serializzato
        
        Args:
            data: Dizionario serializzato
            
        Returns:
            Entity: L'entità deserializzata
        """
        entity = cls(id=data.get("id"), name=data.get("name"))
        
        # Imposta lo stato
        entity.active = data.get("active", True)
        entity.marked_for_removal = data.get("marked_for_removal", False)
        
        # Aggiungi i tag
        for tag in data.get("tags", []):
            entity.add_tag(tag)
            
        # Componenti aggiunti dal metodo chiamante
        
        # Aggiungi le abilità
        entity.abilita = data.get("abilita", {}).copy()
        
        return entity
        
    deserialize = from_dict  # Alias per compatibilità
        
    def __str__(self) -> str:
        """
        Rappresentazione in stringa dell'entità
        
        Returns:
            str: Rappresentazione testuale dell'entità
        """
        return f"{self.name} (ID: {self.id}, Components: {list(self.components.keys())}, Tags: {list(self.tags)})" 