class FiltriInventario:
    """
    Classe che fornisce metodi di filtraggio per gli oggetti dell'inventario.
    Consente di estrarre sottoinsiemi di oggetti in base a vari criteri.
    """
    
    @staticmethod
    def oggetti_per_tipo(inventario, tipo):
        """
        Filtra gli oggetti per tipo specifico.
        
        Args:
            inventario (list): Lista di oggetti dell'inventario
            tipo (str): Tipo di oggetti da filtrare (es. "arma", "armatura", ecc.)
            
        Returns:
            list: Lista di oggetti del tipo specificato
        """
        return [item for item in inventario if hasattr(item, 'tipo') and item.tipo == tipo]
    
    @staticmethod
    def oggetti_equipaggiabili(inventario):
        """
        Filtra gli oggetti equipaggiabili dall'inventario.
        
        Args:
            inventario (list): Lista di oggetti dell'inventario
            
        Returns:
            list: Lista di oggetti equipaggiabili
        """
        return [item for item in inventario 
                if not isinstance(item, str) and hasattr(item, 'tipo') and 
                item.tipo in ["arma", "armatura", "accessorio"]]
    
    @staticmethod
    def oggetti_consumabili(inventario):
        """
        Filtra gli oggetti consumabili dall'inventario.
        
        Args:
            inventario (list): Lista di oggetti dell'inventario
            
        Returns:
            list: Lista di oggetti consumabili
        """
        return [item for item in inventario 
                if not isinstance(item, str) and hasattr(item, 'tipo') and 
                item.tipo == "consumabile"]
    
    @staticmethod
    def oggetti_per_rarita(inventario, rarita):
        """
        Filtra gli oggetti per rarità.
        
        Args:
            inventario (list): Lista di oggetti dell'inventario
            rarita (str): Rarità degli oggetti da filtrare (es. "comune", "raro", "epico")
            
        Returns:
            list: Lista di oggetti della rarità specificata
        """
        return [item for item in inventario 
                if hasattr(item, 'rarita') and item.rarita == rarita]
    
    @staticmethod
    def oggetti_per_valore(inventario, valore_min=0, valore_max=float('inf')):
        """
        Filtra gli oggetti per valore.
        
        Args:
            inventario (list): Lista di oggetti dell'inventario
            valore_min (int): Valore minimo (incluso)
            valore_max (int): Valore massimo (incluso)
            
        Returns:
            list: Lista di oggetti nel range di valore specificato
        """
        return [item for item in inventario 
                if hasattr(item, 'valore') and valore_min <= item.valore <= valore_max]
                
    @staticmethod
    def ordina_per_valore(inventario, decrescente=True):
        """
        Ordina gli oggetti per valore.
        
        Args:
            inventario (list): Lista di oggetti dell'inventario
            decrescente (bool): Se True, ordina in modo decrescente, altrimenti crescente
            
        Returns:
            list: Lista di oggetti ordinata per valore
        """
        return sorted([item for item in inventario if hasattr(item, 'valore')], 
                     key=lambda x: x.valore, 
                     reverse=decrescente) 