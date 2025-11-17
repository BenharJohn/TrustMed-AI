"""
Citation Tracking and Formatting Module
Handles inline citation markers [1], [2] and generates formatted source lists
"""

class CitationTracker:
    """Tracks citations and generates formatted reference lists like research papers"""

    def __init__(self):
        self.citations = []
        self.citation_map = {}  # key: source identifier -> citation number

    def add_citation(self, source_layer, source_detail="Unknown"):
        """
        Add a citation and return the marker (e.g., [1], [2])

        Args:
            source_layer: "UMLS" | "MedC-K" | "MIMIC-IV"
            source_detail: Additional information (file name, note ID, etc.)

        Returns:
            str: Citation marker like "[1]"
        """
        # Create unique key for this source
        key = f"{source_layer}:{source_detail}"

        # If already cited, return existing number
        if key in self.citation_map:
            return f"[{self.citation_map[key]}]"

        # Add new citation
        self.citations.append({
            "layer": source_layer,
            "detail": source_detail
        })

        # Assign citation number (1-indexed)
        citation_num = len(self.citations)
        self.citation_map[key] = citation_num

        return f"[{citation_num}]"

    def format_citations(self):
        """
        Generate formatted citation list

        Returns:
            str: Markdown-formatted citation list
        """
        if not self.citations:
            return ""

        output = "\n\n**Sources:**\n\n"

        for i, cite in enumerate(self.citations, 1):
            layer = cite["layer"]
            detail = cite["detail"]

            if layer == "UMLS":
                output += f"[{i}] UMLS Medical Ontology - {detail}\n"
            elif layer == "MedC-K":
                output += f"[{i}] Medical Knowledge Base (MedC-K) - {detail}\n"
            elif layer == "MIMIC-IV":
                output += f"[{i}] Clinical Case Study (MIMIC-IV) - {detail}\n"
            else:
                output += f"[{i}] {layer} - {detail}\n"

        return output

    def get_citation_count(self):
        """Return number of unique citations"""
        return len(self.citations)

    def has_citations(self):
        """Check if any citations have been added"""
        return len(self.citations) > 0

    def get_layers_used(self):
        """Return list of unique source layers cited"""
        return list(set(cite["layer"] for cite in self.citations))


def extract_source_info(context_data):
    """
    Extract source information from graph context

    Args:
        context_data: Dictionary containing graph context from ret_context_ollama()

    Returns:
        dict: {
            'source_layer': str,
            'source_file': str,
            'entities': list,
            'relationships': list
        }
    """
    # Extract source metadata if available
    source_layer = context_data.get('source_layer', 'Unknown')
    source_file = context_data.get('source_file', 'Medical Knowledge Graph')

    return {
        'source_layer': source_layer,
        'source_file': source_file,
        'entities': context_data.get('entities', []),
        'relationships': context_data.get('relationships', [])
    }
