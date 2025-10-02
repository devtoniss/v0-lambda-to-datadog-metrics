"""
Testes unitários para o serviço de processamento de CSV.
"""

import unittest
import tempfile
import os
from unittest.mock import Mock

from app.src.services.csv_service import CSVService
from app.src.config.settings import Settings


class TestCSVService(unittest.TestCase):
    """Testes para o CSVService."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        # Mock das configurações
        self.settings = Mock(spec=Settings)
        self.csv_service = CSVService(self.settings)
    
    def test_processar_csv_basico(self):
        """Testa processamento básico de CSV."""
        # Criar arquivo CSV temporário
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write('nome_metrica,valor\n')
            f.write('cpu,75.5\n')
            f.write('memoria,80.2\n')
            temp_file = f.name
        
        try:
            # Processar CSV
            metricas = self.csv_service.processar_csv(temp_file, 'ecs')
            
            # Verificações
            self.assertEqual(len(metricas), 2)
            self.assertEqual(metricas[0]['metric'], 'aws.ecs.cpu_utilization')
            self.assertEqual(metricas[0]['points'][0][1], 75.5)
            self.assertEqual(metricas[1]['metric'], 'aws.ecs.memory_utilization')
            
        finally:
            # Limpar arquivo temporário
            os.unlink(temp_file)
    
    def test_processar_tags(self):
        """Testa processamento de tags."""
        tags_resultado = self.csv_service._processar_tags(
            'env:prod,service:api',
            ['source:lambda']
        )
        
        self.assertIn('source:lambda', tags_resultado)
        self.assertIn('env:prod', tags_resultado)
        self.assertIn('service:api', tags_resultado)


if __name__ == '__main__':
    unittest.main()
