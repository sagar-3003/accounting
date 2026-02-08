"""
Ind AS (Indian Accounting Standards) knowledge base
Comprehensive information about Ind AS standards
"""

from typing import List, Dict, Optional


# Comprehensive Ind AS knowledge base
IND_AS_STANDARDS = {
    "1": {
        "number": "1",
        "title": "Presentation of Financial Statements",
        "objective": "To prescribe the basis for presentation of general purpose financial statements to ensure comparability",
        "key_principles": [
            "Fair presentation and compliance with Ind AS",
            "Going concern assumption",
            "Accrual basis of accounting",
            "Materiality and aggregation",
            "Offsetting not permitted unless required by Ind AS",
            "Frequency of reporting - at least annually",
            "Comparative information to be presented"
        ],
        "disclosure_requirements": [
            "Complete set of financial statements",
            "Statement of financial position",
            "Statement of profit and loss",
            "Statement of changes in equity",
            "Statement of cash flows",
            "Notes including accounting policies"
        ]
    },
    "2": {
        "number": "2",
        "title": "Inventories",
        "objective": "To prescribe the accounting treatment for inventories including measurement and cost formulas",
        "key_principles": [
            "Measured at lower of cost and net realizable value",
            "Cost includes purchase price, conversion costs, and other costs",
            "FIFO or weighted average cost formulas",
            "Write-down to NRV when cost exceeds NRV",
            "Reversal of write-down when circumstances change"
        ],
        "disclosure_requirements": [
            "Accounting policies for inventories",
            "Carrying amount by classification",
            "Amount recognized as expense",
            "Write-downs and reversals",
            "Inventories pledged as security"
        ]
    },
    "7": {
        "number": "7",
        "title": "Statement of Cash Flows",
        "objective": "To require information about historical changes in cash and cash equivalents through cash flow statement",
        "key_principles": [
            "Classify cash flows into operating, investing, and financing activities",
            "Operating activities: principal revenue-producing activities",
            "Investing activities: acquisition and disposal of long-term assets",
            "Financing activities: changes in equity and borrowings",
            "Direct or indirect method for operating activities"
        ],
        "disclosure_requirements": [
            "Cash flows from operating, investing, and financing activities",
            "Reconciliation of cash and cash equivalents",
            "Significant non-cash transactions",
            "Components of cash and cash equivalents"
        ]
    },
    "8": {
        "number": "8",
        "title": "Accounting Policies, Changes in Accounting Estimates and Errors",
        "objective": "To prescribe criteria for selecting and changing accounting policies, accounting for changes in estimates and errors",
        "key_principles": [
            "Select and apply accounting policies consistently",
            "Change only if required by Ind AS or results in more relevant information",
            "Apply changes retrospectively",
            "Changes in estimates applied prospectively",
            "Correct material prior period errors retrospectively"
        ],
        "disclosure_requirements": [
            "Nature of change in accounting policy",
            "Reasons for change",
            "Amount of adjustment for current and prior periods",
            "Nature and amount of change in accounting estimate"
        ]
    },
    "10": {
        "number": "10",
        "title": "Events after the Reporting Period",
        "objective": "To prescribe when to adjust financial statements for events after reporting period and disclosures required",
        "key_principles": [
            "Adjusting events: provide evidence of conditions at end of reporting period",
            "Non-adjusting events: indicative of conditions after reporting period",
            "Adjust for adjusting events",
            "Disclose non-adjusting events if material",
            "Update going concern assessment"
        ],
        "disclosure_requirements": [
            "Date of authorization of financial statements",
            "Nature and financial impact of material non-adjusting events",
            "Dividends declared after reporting period"
        ]
    },
    "12": {
        "number": "12",
        "title": "Income Taxes",
        "objective": "To prescribe accounting treatment for income taxes including current and deferred tax",
        "key_principles": [
            "Recognize current tax liability for current period",
            "Recognize deferred tax for temporary differences",
            "Deferred tax asset for unused tax losses and credits",
            "Measurement at tax rates expected to apply",
            "Review deferred tax assets at each reporting date"
        ],
        "disclosure_requirements": [
            "Major components of tax expense/income",
            "Deferred tax assets and liabilities",
            "Reconciliation of tax rate",
            "Unused tax losses and credits"
        ]
    },
    "16": {
        "number": "16",
        "title": "Property, Plant and Equipment",
        "objective": "To prescribe accounting treatment for property, plant and equipment",
        "key_principles": [
            "Recognize when probable future economic benefits and cost measurable",
            "Measure initially at cost",
            "Subsequently: cost model or revaluation model",
            "Depreciate systematically over useful life",
            "Review useful life, residual value, and depreciation method annually"
        ],
        "disclosure_requirements": [
            "Measurement bases",
            "Depreciation methods and useful lives",
            "Reconciliation of carrying amounts",
            "Restrictions and pledges"
        ]
    },
    "19": {
        "number": "19",
        "title": "Employee Benefits",
        "objective": "To prescribe accounting and disclosure for employee benefits",
        "key_principles": [
            "Short-term benefits: recognize undiscounted amount as expense",
            "Post-employment benefits: defined contribution or defined benefit plans",
            "Defined contribution: recognize contributions as expense",
            "Defined benefit: use actuarial valuation",
            "Other long-term benefits and termination benefits"
        ],
        "disclosure_requirements": [
            "Nature and amount of expense",
            "Defined benefit plan disclosures",
            "Actuarial assumptions",
            "Sensitivity analysis"
        ]
    },
    "115": {
        "number": "115",
        "title": "Revenue from Contracts with Customers",
        "objective": "To establish principles for reporting useful information about nature, amount, timing of revenue and cash flows",
        "key_principles": [
            "5-step model: identify contract, identify performance obligations, determine price, allocate price, recognize revenue",
            "Recognize when performance obligation satisfied",
            "Control transferred to customer",
            "Over time or at a point in time",
            "Variable consideration and time value of money"
        ],
        "disclosure_requirements": [
            "Disaggregation of revenue",
            "Contract balances",
            "Performance obligations",
            "Transaction price allocation",
            "Costs to obtain or fulfill contracts"
        ]
    },
    "116": {
        "number": "116",
        "title": "Leases",
        "objective": "To ensure lessees and lessors provide relevant information that faithfully represents lease transactions",
        "key_principles": [
            "Lessee: recognize right-of-use asset and lease liability",
            "Except short-term and low-value leases",
            "Lessor: classify as finance or operating lease",
            "Finance lease: recognize lease receivable",
            "Operating lease: recognize lease income on straight-line basis"
        ],
        "disclosure_requirements": [
            "Nature of leasing activities",
            "Maturity analysis of lease liabilities",
            "Lease income by type",
            "Risk management strategy"
        ]
    },
    "20": {
        "number": "20",
        "title": "Accounting for Government Grants",
        "objective": "To prescribe accounting for government grants and disclosure of government assistance",
        "key_principles": [
            "Recognize when reasonable assurance of compliance and grant will be received",
            "Recognize systematically over periods of related costs",
            "Capital approach or income approach",
            "Repayment of grant as change in estimate"
        ],
        "disclosure_requirements": [
            "Accounting policy",
            "Nature and extent of grants",
            "Unfulfilled conditions and contingencies"
        ]
    },
    "21": {
        "number": "21",
        "title": "The Effects of Changes in Foreign Exchange Rates",
        "objective": "To prescribe how to include foreign currency transactions and foreign operations in financial statements",
        "key_principles": [
            "Determine functional currency",
            "Translate foreign currency transactions at spot rate",
            "Monetary items at closing rate at each reporting date",
            "Exchange differences in profit or loss or OCI",
            "Translation of foreign operations"
        ],
        "disclosure_requirements": [
            "Amount of exchange differences",
            "Functional currency and reasons for change",
            "Presentation currency if different"
        ]
    },
    "23": {
        "number": "23",
        "title": "Borrowing Costs",
        "objective": "To prescribe accounting treatment for borrowing costs",
        "key_principles": [
            "Capitalize borrowing costs directly attributable to qualifying assets",
            "Qualifying asset: takes substantial period to get ready for use or sale",
            "Suspend capitalization during extended periods of delay",
            "Cease when substantially all activities complete",
            "Other borrowing costs expensed"
        ],
        "disclosure_requirements": [
            "Amount of borrowing costs capitalized",
            "Capitalization rate used"
        ]
    },
    "24": {
        "number": "24",
        "title": "Related Party Disclosures",
        "objective": "To ensure financial statements contain disclosures necessary to draw attention to possibility of related party effects",
        "key_principles": [
            "Identify related party relationships",
            "Disclose relationships even if no transactions",
            "Disclose transactions and outstanding balances",
            "Key management personnel compensation",
            "Parent and ultimate controlling party"
        ],
        "disclosure_requirements": [
            "Nature of related party relationship",
            "Transactions by type",
            "Outstanding balances and terms",
            "Compensation of key management personnel"
        ]
    },
    "27": {
        "number": "27",
        "title": "Separate Financial Statements",
        "objective": "To prescribe accounting and disclosure requirements for investments in subsidiaries, joint ventures, and associates",
        "key_principles": [
            "Separate financial statements: parent accounting for investments",
            "Account at cost or in accordance with Ind AS 109",
            "Dividends recognized when right to receive established",
            "Not consolidated financial statements"
        ],
        "disclosure_requirements": [
            "Accounting policy for investments",
            "List of significant investments",
            "Indication of listed investments and fair values"
        ]
    },
    "28": {
        "number": "28",
        "title": "Investments in Associates and Joint Ventures",
        "objective": "To prescribe accounting for investments in associates and joint ventures and requirements for equity method",
        "key_principles": [
            "Apply equity method unless exempted",
            "Initially at cost then adjusted for post-acquisition changes",
            "Investor's share of profit or loss in P&L",
            "Investor's share of OCI in OCI",
            "Discontinue when ceases to be associate or joint venture"
        ],
        "disclosure_requirements": [
            "Nature, extent, and financial effects",
            "Summarized financial information",
            "Contingent liabilities",
            "Unrecognized share of losses"
        ]
    },
    "32": {
        "number": "32",
        "title": "Financial Instruments: Presentation",
        "objective": "To establish principles for presenting financial instruments as liabilities or equity",
        "key_principles": [
            "Classify as liability or equity based on substance",
            "Equity: residual interest after deducting liabilities",
            "Compound instruments: separate liability and equity components",
            "Treasury shares deducted from equity",
            "Offsetting financial assets and liabilities when specific criteria met"
        ],
        "disclosure_requirements": [
            "Carrying amounts by category",
            "Information about compound instruments",
            "Details about offsetting"
        ]
    },
    "33": {
        "number": "33",
        "title": "Earnings per Share",
        "objective": "To prescribe principles for determining and presenting earnings per share",
        "key_principles": [
            "Basic EPS: profit attributable to ordinary equity holders / weighted average shares",
            "Diluted EPS: adjust for dilutive potential ordinary shares",
            "Present both basic and diluted EPS",
            "Adjusted retrospectively for changes in capital structure"
        ],
        "disclosure_requirements": [
            "Basic and diluted EPS",
            "Reconciliation of numerators and denominators",
            "Antidilutive potential shares not included"
        ]
    },
    "36": {
        "number": "36",
        "title": "Impairment of Assets",
        "objective": "To prescribe procedures to ensure assets not carried above recoverable amount",
        "key_principles": [
            "Test for impairment when indicators exist",
            "Goodwill and intangibles with indefinite life: annual test",
            "Recoverable amount: higher of fair value less costs of disposal and value in use",
            "Recognize impairment loss immediately",
            "Reverse if increase in recoverable amount (except goodwill)"
        ],
        "disclosure_requirements": [
            "Impairment losses recognized and reversed",
            "Events leading to impairment",
            "Segment reporting of impairment",
            "Key assumptions for value in use"
        ]
    },
    "37": {
        "number": "37",
        "title": "Provisions, Contingent Liabilities and Contingent Assets",
        "objective": "To ensure appropriate recognition criteria and measurement bases for provisions, contingent liabilities and assets",
        "key_principles": [
            "Recognize provision when: present obligation, probable outflow, reliable estimate",
            "Measure at best estimate of expenditure",
            "Review and adjust provisions at each reporting date",
            "Contingent liability: disclose unless remote",
            "Contingent asset: disclose if probable"
        ],
        "disclosure_requirements": [
            "Carrying amount and changes",
            "Nature and timing of settlement",
            "Uncertainties and reimbursements",
            "Contingent liabilities and assets"
        ]
    },
    "38": {
        "number": "38",
        "title": "Intangible Assets",
        "objective": "To prescribe accounting treatment for intangible assets not dealt with specifically in another Ind AS",
        "key_principles": [
            "Recognize when: identifiable, control, future economic benefits, cost measurable",
            "Measure initially at cost",
            "Subsequently: cost model or revaluation model",
            "Finite or indefinite useful life",
            "Amortize finite-lived assets over useful life"
        ],
        "disclosure_requirements": [
            "Useful lives or amortization rates",
            "Amortization methods",
            "Reconciliation of carrying amounts",
            "Individually material intangible assets"
        ]
    },
    "40": {
        "number": "40",
        "title": "Investment Property",
        "objective": "To prescribe accounting treatment for investment property and related disclosure",
        "key_principles": [
            "Property held to earn rentals or capital appreciation",
            "Initially measure at cost",
            "Subsequently: fair value model or cost model",
            "Fair value model: changes in fair value in P&L",
            "Cost model: similar to Ind AS 16"
        ],
        "disclosure_requirements": [
            "Whether fair value or cost model",
            "Methods and assumptions for fair value",
            "Reconciliation of carrying amounts",
            "Rental income and operating expenses"
        ]
    },
    "101": {
        "number": "101",
        "title": "First-time Adoption of Indian Accounting Standards",
        "objective": "To ensure first Ind AS financial statements contain high quality information",
        "key_principles": [
            "Prepare opening Ind AS balance sheet at transition date",
            "Apply all Ind AS retrospectively",
            "Mandatory exceptions to retrospective application",
            "Optional exemptions from requirements",
            "Explain transition to Ind AS including reconciliations"
        ],
        "disclosure_requirements": [
            "Reconciliation of equity",
            "Reconciliation of profit or loss",
            "Explanation of material adjustments",
            "Use of optional exemptions"
        ]
    },
    "102": {
        "number": "102",
        "title": "Share-based Payment",
        "objective": "To specify financial reporting for share-based payment transactions",
        "key_principles": [
            "Measure goods/services and corresponding equity increase at fair value",
            "Equity-settled: fair value at grant date",
            "Cash-settled: fair value at each reporting date",
            "Recognize over vesting period",
            "Modify for non-market vesting conditions"
        ],
        "disclosure_requirements": [
            "Nature and extent of arrangements",
            "Determination of fair value",
            "Effect on profit or loss and financial position"
        ]
    },
    "103": {
        "number": "103",
        "title": "Business Combinations",
        "objective": "To improve relevance, reliability and comparability of information about business combinations",
        "key_principles": [
            "Apply acquisition method",
            "Identify acquirer, acquisition date, consideration transferred",
            "Recognize and measure identifiable assets, liabilities, and NCI",
            "Recognize goodwill or gain from bargain purchase",
            "Measure at fair value at acquisition date"
        ],
        "disclosure_requirements": [
            "Name and description of acquiree",
            "Acquisition date and percentage acquired",
            "Primary reasons and how control obtained",
            "Fair values of consideration and assets acquired"
        ]
    },
    "104": {
        "number": "104",
        "title": "Insurance Contracts",
        "objective": "To specify financial reporting for insurance contracts",
        "key_principles": [
            "Exemptions from Ind AS framework for insurance contracts",
            "Minimum requirements for insurance contracts",
            "Embedded derivatives in insurance contracts",
            "Discretionary participation features",
            "Liability adequacy test"
        ],
        "disclosure_requirements": [
            "Accounting policies for insurance contracts",
            "Recognized assets, liabilities, income and expense",
            "Process for determining assumptions",
            "Changes in assumptions"
        ]
    },
    "105": {
        "number": "105",
        "title": "Non-current Assets Held for Sale and Discontinued Operations",
        "objective": "To specify accounting for assets held for sale and presentation of discontinued operations",
        "key_principles": [
            "Classify as held for sale when available for sale and sale highly probable",
            "Measure at lower of carrying amount and fair value less costs to sell",
            "Do not depreciate",
            "Present separately in balance sheet",
            "Discontinued operation: component disposed or classified as held for sale"
        ],
        "disclosure_requirements": [
            "Description and carrying amounts",
            "Facts and circumstances of sale",
            "Segment in which presented",
            "Single amount for discontinued operations in P&L"
        ]
    },
    "106": {
        "number": "106",
        "title": "Exploration for and Evaluation of Mineral Resources",
        "objective": "To specify financial reporting for exploration and evaluation of mineral resources",
        "key_principles": [
            "Develop accounting policy for recognition",
            "Measure at cost",
            "Test for impairment when indicators exist",
            "Classify as tangible or intangible",
            "Reclassify when technical feasibility and commercial viability demonstrable"
        ],
        "disclosure_requirements": [
            "Accounting policies",
            "Amounts recognized",
            "Impairment losses"
        ]
    },
    "107": {
        "number": "107",
        "title": "Financial Instruments: Disclosures",
        "objective": "To require disclosures to evaluate significance of financial instruments and nature/extent of risks",
        "key_principles": [
            "Disclose by category of financial instrument",
            "Credit risk, liquidity risk, and market risk",
            "Risk management objectives and policies",
            "Sensitivity analysis for market risks",
            "Fair value hierarchy"
        ],
        "disclosure_requirements": [
            "Carrying amounts by category",
            "Nature and extent of risks",
            "Risk management objectives",
            "Quantitative data about exposures",
            "Fair value measurements"
        ]
    },
    "108": {
        "number": "108",
        "title": "Operating Segments",
        "objective": "To require disclosure to enable evaluation of nature and financial effects of business activities and economic environments",
        "key_principles": [
            "Operating segment: component that earns revenue/incurs expenses",
            "Operating results regularly reviewed by CODM",
            "Discrete financial information available",
            "Reportable segment: meets quantitative thresholds",
            "Reconcile segment information to entity totals"
        ],
        "disclosure_requirements": [
            "General information about segments",
            "Profit or loss, assets, and liabilities",
            "Measurement basis",
            "Reconciliations to entity amounts",
            "Entity-wide disclosures"
        ]
    },
    "109": {
        "number": "109",
        "title": "Financial Instruments",
        "objective": "To establish principles for financial reporting of financial assets and liabilities",
        "key_principles": [
            "Classification based on business model and cash flow characteristics",
            "Three categories: amortized cost, FVOCI, FVPL",
            "SPPI test: solely payments of principal and interest",
            "Expected credit loss model for impairment",
            "Hedge accounting provisions"
        ],
        "disclosure_requirements": [
            "Carrying amounts by category",
            "Gains and losses",
            "Interest income and impairment",
            "Hedge accounting disclosures"
        ]
    },
    "110": {
        "number": "110",
        "title": "Consolidated Financial Statements",
        "objective": "To establish principles for presentation and preparation of consolidated financial statements",
        "key_principles": [
            "Consolidate all subsidiaries",
            "Control: power, exposure to variable returns, ability to use power",
            "Uniform accounting policies",
            "Eliminate intragroup transactions",
            "NCI presented in equity separately from parent"
        ],
        "disclosure_requirements": [
            "Composition of group",
            "NCI in each subsidiary",
            "Restrictions on consolidated assets",
            "Significant judgments in determining control"
        ]
    },
    "111": {
        "number": "111",
        "title": "Joint Arrangements",
        "objective": "To establish principles for financial reporting by entities with interests in joint arrangements",
        "key_principles": [
            "Determine type: joint operation or joint venture",
            "Joint operation: rights to assets and obligations for liabilities",
            "Joint venture: rights to net assets",
            "Joint operation: recognize assets, liabilities, revenue, expenses",
            "Joint venture: apply equity method"
        ],
        "disclosure_requirements": [
            "Nature, extent, and financial effects",
            "Commitments and contingent liabilities",
            "Summarized financial information of joint ventures"
        ]
    },
    "112": {
        "number": "112",
        "title": "Disclosure of Interests in Other Entities",
        "objective": "To require disclosure to evaluate nature of interests in other entities and associated risks",
        "key_principles": [
            "Disclose for subsidiaries, joint arrangements, associates, and unconsolidated structured entities",
            "Significant judgments and assumptions",
            "Nature of interests and associated risks",
            "Effects on financial position, performance, and cash flows"
        ],
        "disclosure_requirements": [
            "Significant judgments in determining control/influence",
            "Interests in subsidiaries, joint arrangements, and associates",
            "Interests in unconsolidated structured entities",
            "Summarized financial information",
            "Restrictions and risks"
        ]
    },
    "113": {
        "number": "113",
        "title": "Fair Value Measurement",
        "objective": "To define fair value, establish framework for measuring fair value, and require disclosures",
        "key_principles": [
            "Fair value: price to sell asset or transfer liability in orderly transaction",
            "Market participant assumptions",
            "Exit price from principal or most advantageous market",
            "Fair value hierarchy: Level 1, 2, and 3 inputs",
            "Highest and best use for non-financial assets"
        ],
        "disclosure_requirements": [
            "Fair value measurement and hierarchy level",
            "Valuation techniques and inputs",
            "Sensitivity of Level 3 measurements",
            "Transfers between levels"
        ]
    },
    "114": {
        "number": "114",
        "title": "Regulatory Deferral Accounts",
        "objective": "To specify financial reporting for regulatory deferral account balances",
        "key_principles": [
            "Optional exemption for first-time adopters",
            "Continue to recognize regulatory deferral accounts",
            "Present separately from other assets and liabilities",
            "Movement in regulatory deferral accounts in OCI or P&L",
            "Do not apply other Ind AS to regulatory deferral accounts"
        ],
        "disclosure_requirements": [
            "Nature and regulatory environment",
            "Accounting policies",
            "Balances and movements",
            "Rate regulation details"
        ]
    }
}


# Mapping of old Indian GAAP to Ind AS
GAAP_TO_IND_AS_MAPPING = {
    "AS 1": "Ind AS 1 - Presentation of Financial Statements",
    "AS 2": "Ind AS 2 - Inventories",
    "AS 3": "Ind AS 7 - Statement of Cash Flows",
    "AS 4": "Ind AS 10 - Events after the Reporting Period",
    "AS 5": "Ind AS 8 - Accounting Policies, Changes in Estimates and Errors (partially), Ind AS 10 (partially)",
    "AS 7": "Ind AS 16 - Property, Plant and Equipment; Ind AS 2 - Inventories",
    "AS 9": "Ind AS 115 - Revenue from Contracts with Customers",
    "AS 10": "Ind AS 16 - Property, Plant and Equipment",
    "AS 11": "Ind AS 115 - Revenue from Contracts with Customers (construction contracts)",
    "AS 12": "Ind AS 20 - Accounting for Government Grants",
    "AS 13": "Ind AS 27 - Separate Financial Statements; Ind AS 28 - Investments in Associates",
    "AS 14": "Ind AS 33 - Earnings per Share",
    "AS 15": "Ind AS 19 - Employee Benefits",
    "AS 16": "Ind AS 38 - Intangible Assets",
    "AS 17": "Ind AS 108 - Operating Segments",
    "AS 18": "Ind AS 24 - Related Party Disclosures",
    "AS 19": "Ind AS 116 - Leases",
    "AS 20": "Ind AS 33 - Earnings per Share (diluted)",
    "AS 21": "Ind AS 110 - Consolidated Financial Statements",
    "AS 22": "Ind AS 12 - Income Taxes",
    "AS 23": "Ind AS 103 - Business Combinations; Ind AS 110",
    "AS 24": "Ind AS 105 - Non-current Assets Held for Sale and Discontinued Operations",
    "AS 25": "Ind AS 108 - Operating Segments (interim reporting)",
    "AS 26": "Ind AS 38 - Intangible Assets",
    "AS 27": "Ind AS 111 - Joint Arrangements",
    "AS 28": "Ind AS 36 - Impairment of Assets",
    "AS 29": "Ind AS 37 - Provisions, Contingent Liabilities and Contingent Assets",
    "AS 30": "Ind AS 109 - Financial Instruments",
    "AS 31": "Ind AS 32 - Financial Instruments: Presentation; Ind AS 109",
    "AS 32": "Ind AS 109 - Financial Instruments"
}


def search_ind_as(keyword: str) -> List[Dict]:
    """
    Search Ind AS standards by keyword
    
    Args:
        keyword: Search keyword
        
    Returns:
        List of matching standards
    """
    keyword = keyword.lower()
    results = []
    
    for std_num, std_data in IND_AS_STANDARDS.items():
        # Search in title
        if keyword in std_data["title"].lower():
            results.append(std_data)
            continue
        
        # Search in objective
        if keyword in std_data["objective"].lower():
            results.append(std_data)
            continue
        
        # Search in key principles
        for principle in std_data["key_principles"]:
            if keyword in principle.lower():
                results.append(std_data)
                break
    
    return results


def get_ind_as_standard(number: str) -> Optional[Dict]:
    """
    Get Ind AS standard by number
    
    Args:
        number: Standard number (e.g., "1", "115")
        
    Returns:
        Standard details or None
    """
    return IND_AS_STANDARDS.get(number)


def get_all_ind_as_standards() -> Dict:
    """
    Get all Ind AS standards
    
    Returns:
        Dictionary of all standards
    """
    return IND_AS_STANDARDS


def map_gaap_to_ind_as(as_number: str) -> Optional[str]:
    """
    Map old AS (Indian GAAP) to Ind AS
    
    Args:
        as_number: Old AS number (e.g., "AS 1")
        
    Returns:
        Corresponding Ind AS or None
    """
    return GAAP_TO_IND_AS_MAPPING.get(as_number)


class IndASModule:
    """Wrapper class for Ind AS module to provide object-oriented interface"""
    
    def __init__(self):
        """Initialize Ind AS module"""
        pass
    
    def search_standards(self, keyword: str) -> List[Dict]:
        """Search Ind AS standards by keyword"""
        return search_ind_as(keyword)
    
    def get_standard_details(self, number: str) -> Optional[Dict]:
        """Get Ind AS standard by number"""
        return get_ind_as_standard(number)
    
    def get_all_standards(self) -> List[Dict]:
        """Get all Ind AS standards as a list"""
        return [std for std in IND_AS_STANDARDS.values()]
    
    def map_gaap_to_ind_as(self, as_number: str) -> Optional[str]:
        """Map old AS (Indian GAAP) to Ind AS"""
        return map_gaap_to_ind_as(as_number)

