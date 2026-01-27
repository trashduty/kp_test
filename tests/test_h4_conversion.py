"""
Tests for h4 header conversion in convert_to_html function
"""
import sys
import os

# Add parent directory to path to import generate_previews
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_previews import convert_to_html


def test_h4_headers_convert_to_html():
    """Test that #### markdown headers convert to <h4> HTML tags"""
    markdown = """#### Setting the Stage
Some content here.
#### Breaking Down the Spread
More content.
#### Offensive Firepower
Even more content."""
    
    html = convert_to_html(markdown)
    
    # Check that h4 tags are created
    assert '<h4>Setting the Stage</h4>' in html
    assert '<h4>Breaking Down the Spread</h4>' in html
    assert '<h4>Offensive Firepower</h4>' in html
    
    # Check that #### markdown syntax is not present
    assert '####' not in html
    
    print("✓ h4 headers convert to HTML correctly")


def test_all_header_levels_convert():
    """Test that all header levels (h1-h4) convert correctly"""
    markdown = """# Main Title
## Section Title
### Subsection Title
#### Detail Header
Some content."""
    
    html = convert_to_html(markdown)
    
    # Check all header levels
    assert '<h1>Main Title</h1>' in html
    assert '<h2>Section Title</h2>' in html
    assert '<h3>Subsection Title</h3>' in html
    assert '<h4>Detail Header</h4>' in html
    
    # Check no markdown syntax remains
    assert '####' not in html
    assert '###' not in html
    assert '##' not in html
    # Note: single # might appear in content, so we only check multi-hash
    
    print("✓ All header levels convert correctly")


def test_h4_headers_with_newlines():
    """Test h4 headers with different newline patterns"""
    markdown = """#### Tempo & Playing Style

Some content about tempo.

#### The Interior Battle

Content about interior play."""
    
    html = convert_to_html(markdown)
    
    assert '<h4>Tempo & Playing Style</h4>' in html
    assert '<h4>The Interior Battle</h4>' in html
    assert '####' not in html
    
    print("✓ h4 headers with newlines convert correctly")


def test_h4_headers_with_special_characters():
    """Test h4 headers with special characters like & and apostrophes"""
    markdown = """#### X-Factors & Intangibles
Content here."""
    
    html = convert_to_html(markdown)
    
    assert '<h4>X-Factors & Intangibles</h4>' in html
    assert '####' not in html
    
    print("✓ h4 headers with special characters convert correctly")


if __name__ == '__main__':
    test_h4_headers_convert_to_html()
    test_all_header_levels_convert()
    test_h4_headers_with_newlines()
    test_h4_headers_with_special_characters()
    print("\n✅ All h4 conversion tests passed!")
