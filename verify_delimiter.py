import sys
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, '/mnt/d/prj/RSSHub-python')

# Mock cache before importing randomline
sys.modules['rsshub.extensions'] = MagicMock()
# Use a valid mock for cache.get to avoid attribute errors if accessed
sys.modules['rsshub.extensions'].cache.get.return_value = None

from rsshub.spiders.randomline.randomline import ctx

class TestRandomlineDelimiter(unittest.TestCase):
    def test_comma_default(self):
        # Mock requests.get
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            # CSV content with commas
            mock_response.text = "col1,col2\nval1,val2\nval3,val4"
            mock_get.return_value = mock_response
            
            # Call ctx without delimiter (should default to comma)
            result = ctx(url="http://example.com/test.csv")
            
            # Check if parsing was successful
            self.assertEqual(len(result['items']), 1)
            item = result['items'][0]
            # Title should come from first column by default
            self.assertIn(item['title'], ['val1', 'val3'])

    def test_tab_delimiter(self):
        # Mock requests.get
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            # CSV content with tabs
            mock_response.text = "col1\tcol2\nval1\tval2\nval3\tval4"
            mock_get.return_value = mock_response
            
            # Call ctx with delimiter='tab'
            result = ctx(url="http://example.com/test.tsv", delimiter='tab')
            
            # Check if parsing was successful
            self.assertEqual(len(result['items']), 1)
            item = result['items'][0]
            # Should correctly identify columns
            self.assertIn(item['title'], ['val1', 'val3'])
            # Description should contain the other column
            self.assertIn('col2:', item['description'])

    def test_custom_delimiter(self):
        # Mock requests.get
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            # CSV content with semicolons
            mock_response.text = "col1;col2\nval1;val2"
            mock_get.return_value = mock_response
            
            # Call ctx with delimiter=';'
            result = ctx(url="http://example.com/test.txt", delimiter=';')
            
            # Check if parsing was successful
            self.assertEqual(len(result['items']), 1)
            item = result['items'][0]
            self.assertEqual(item['title'], 'val1')

if __name__ == '__main__':
    unittest.main()
