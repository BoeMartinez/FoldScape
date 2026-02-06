#!/usr/bin/env python3
"""
Categorize repos in repos.json based on their purpose.
"""

import json

# Category assignments based on tool purpose
CATEGORY_MAP = {
    # Infrastructure - tools for computation, data handling, visualization
    "biopython/biopython": "Infrastructure",
    "schrodinger/pymol-open-source": "Infrastructure",
    "openmm/openmm": "Infrastructure",
    "pengzhangzhi/faplm": "Infrastructure",  # Efficient PLM implementation
    "pachterlab/gget": "Infrastructure",  # Database querying

    # Core Methods - Structure Prediction
    "google-deepmind/alphafold": "Core Methods",
    "google-deepmind/alphafold3": "Core Methods",
    "aqlaboratory/openfold": "Core Methods",
    "lucidrains/alphafold3-pytorch": "Core Methods",
    "Ligo-Biosciences/AlphaFold3": "Core Methods",
    "kyegomez/Open-AF3": "Core Methods",
    "baker-laboratory/RoseTTAFold-All-Atom": "Core Methods",
    "uw-ipd/RoseTTAFold2": "Core Methods",
    "dptech-corp/Uni-Fold": "Core Methods",
    "HeliXonProtein/OmegaFold": "Core Methods",
    "facebookresearch/esm": "Core Methods",
    "evolutionaryscale/esm": "Core Methods",

    # Core Methods - Generative Design
    "RosettaCommons/RFdiffusion": "Core Methods",
    "generatebio/chroma": "Core Methods",
    "jasonkyuyim/se3_diffusion": "Core Methods",
    "microsoft/protein-frame-flow": "Core Methods",
    "RosettaCommons/protein_generator": "Core Methods",
    "bjing2016/alphaflow": "Core Methods",
    "escalante-bio/mosaic": "Core Methods",

    # Core Methods - Sequence Design / Inverse Folding
    "dauparas/ProteinMPNN": "Core Methods",
    "richardshuai/fampnn": "Core Methods",
    "oxpig/AntiFold": "Core Methods",

    # Core Methods - Language Models
    "agemagician/ProtTrans": "Core Methods",
    "westlake-repl/SaProt": "Core Methods",
    "mheinzinger/ProstT5": "Core Methods",
    "bytedance/dplm": "Core Methods",
    "agemagician/Ankh": "Core Methods",
    "PKU-YuanGroup/ProLLaMA": "Core Methods",
    "westlake-repl/ProTrek": "Core Methods",
    "rs239/abmap": "Core Methods",
    "ElanaPearl/InterPLM": "Core Methods",
    "salesforce/provis": "Core Methods",

    # Core Methods - Other prediction/design tools
    "zrqiao/NeuralPLexer": "Core Methods",
    "patrickbryant1/Umol": "Core Methods",
    "patrickbryant1/RareFold": "Core Methods",
    "LPDI-EPFL/masif-neosurf": "Core Methods",
    "OATML-Markslab/ProteinNPT": "Core Methods",
    "chao1224/ProteinDT": "Core Methods",
    "ml4bio/Dense-Homolog-Retrieval": "Core Methods",

    # Applications - Binder/Antibody Design
    "martinpacesa/BindCraft": "Applications",
    "patrickbryant1/EvoBind": "Applications",

    # Applications - PPI Prediction
    "FreshAirTonight/af2complex": "Applications",
    "CongLabCode/RoseTTAFold2-PPI": "Applications",
    "samsledje/D-SCRIPT": "Applications",

    # Applications - Drug Discovery / Docking
    "HannesStark/EquiBind": "Applications",
    "rdk/p2rank": "Applications",
    "PDB-REDO/alphafill": "Applications",

    # Applications - Benchmarks
    "BioinfoMachineLearning/PoseBench": "Applications",
    "A4Bio/ProteinInvBench": "Applications",
    "bytedance/PXDesignBench": "Applications",
    "J-SNACKKB/FLIP": "Applications",

    # Applications - Accessibility / Pipelines
    "sokrypton/ColabFold": "Applications",
    "sokrypton/ColabDesign": "Applications",
    "Graylab/DL4Proteins-notebooks": "Applications",
    "Hanziwww/AlphaFold3-GUI": "Applications",
    "westlake-repl/SaprotHub": "Applications",
    "martinez-zacharya/TRILL": "Applications",
    "MSDLLCpapers/ovo": "Applications",
    "zjunlp/Mol-Instructions": "Applications",
}

def main():
    # Load repos
    with open('data/repos.json', 'r', encoding='utf-8') as f:
        repos = json.load(f)

    categorized = 0
    uncategorized = []

    for repo in repos:
        repo_id = repo['repo_id']
        if repo_id in CATEGORY_MAP:
            repo['classification']['category'] = CATEGORY_MAP[repo_id]
            categorized += 1
        else:
            uncategorized.append(repo_id)

    # Save updated repos
    with open('data/repos.json', 'w', encoding='utf-8') as f:
        json.dump(repos, f, indent=2, ensure_ascii=False)

    print(f"Categorized: {categorized}/{len(repos)} repos")

    if uncategorized:
        print(f"\nUncategorized ({len(uncategorized)}):")
        for r in uncategorized:
            print(f"  - {r}")

    # Summary by category
    from collections import Counter
    categories = Counter(repo['classification']['category'] for repo in repos if repo['classification']['category'])
    print("\nCategory breakdown:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

if __name__ == "__main__":
    main()
