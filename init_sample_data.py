# =============================================================================
# init_sample_data.py  —  ZTB Super App sample data initialisation
# Run AFTER init_db.py (which creates the tables).
# =============================================================================

# ---------------------------------------------------------------------------
# IMPORTS & SETUP
# ---------------------------------------------------------------------------
from werkzeug.security import generate_password_hash
from app import app, db
from models import (
    Admin, ValueProp, Asset, TestCase, POVPlanner, Roadblock,
    Question, QuestionCategory, QuestionOption, AssessmentConfig,
)


def main():
    """Populate the database with realistic demo/test data."""
    with app.app_context():

        # ===================================================================
        # 1. ADMIN USER
        # Create the default admin account if it doesn't already exist.
        # ===================================================================
        if not Admin.query.filter_by(username="admin").first():
            admin = Admin(
                username="admin",
                password=generate_password_hash("admin123"),
            )
            db.session.add(admin)
            db.session.commit()
            print("  ✔ Admin user created.")
        else:
            print("  – Admin user already exists, skipping.")

        # ===================================================================
        # 2. VALUE PROPS
        # Core business-value propositions for Zscaler ZTB (Zero Trust Branch).
        # mandatory=True props are always shown; False = contextual/optional.
        # ===================================================================
        value_props_data = [
            {
                "title": "Eliminate MPLS Costs",
                "description": "Replace expensive MPLS circuits with broadband + ZT security",
                "business_value": "Cost Reduction",
                "mandatory": True,
            },
            {
                "title": "Simplified Branch Networking",
                "description": "Remove branch firewalls and routers",
                "business_value": "Operational Efficiency",
                "mandatory": True,
            },
            {
                "title": "Zero Trust Security Posture",
                "description": "Apply least-privilege access at every branch",
                "business_value": "Risk Reduction",
                "mandatory": True,
            },
            {
                "title": "SD-WAN Integration",
                "description": "Native integration with leading SD-WAN vendors",
                "business_value": "Flexibility",
                "mandatory": False,
            },
            {
                "title": "Unified Policy Management",
                "description": "Single pane of glass for all branch policies",
                "business_value": "Operational Efficiency",
                "mandatory": False,
            },
            {
                "title": "Cloud-First Architecture",
                "description": "Direct-to-cloud access without backhauling",
                "business_value": "Performance",
                "mandatory": False,
            },
        ]

        vp_objects = []
        for vp_data in value_props_data:
            existing = ValueProp.query.filter_by(title=vp_data["title"]).first()
            if not existing:
                vp = ValueProp(**vp_data)
                db.session.add(vp)
                vp_objects.append(vp)
            else:
                vp_objects.append(existing)
        db.session.commit()
        print(f"  ✔ Value props seeded ({len(value_props_data)} entries).")
        # ===================================================================
        # 3. ASSETS
        # Sales and technical collateral linked to ZTB use cases.
        # ===================================================================
        assets_data = [
            {
                "title": "Zscaler ZTB Datasheet",
                "asset_type": "PDF",
                "url": "https://www.zscaler.com/resources/data-sheets/ztb",
                "description": "Official ZTB product datasheet",
            },
            {
                "title": "ZTB ROI Calculator",
                "asset_type": "Tool",
                "url": "https://www.zscaler.com/roi",
                "description": "Interactive ROI calculator for ZTB",
            },
            {
                "title": "ZTB Demo Video",
                "asset_type": "Video",
                "url": "https://www.zscaler.com/demo/ztb",
                "description": "5-minute product overview",
            },
            {
                "title": "ZTB Reference Architecture",
                "asset_type": "Whitepaper",
                "url": "https://www.zscaler.com/resources/ztb-arch",
                "description": "Technical reference architecture",
            },
            {
                "title": "MPLS vs ZTB TCO Comparison",
                "asset_type": "PDF",
                "url": "https://www.zscaler.com/resources/tco",
                "description": "Total cost of ownership comparison",
            },
            {
                "title": "ZTB Customer Case Study",
                "asset_type": "PDF",
                "url": "https://www.zscaler.com/customers/ztb",
                "description": "Fortune 500 ZTB deployment case study",
            },
        ]

        asset_objects = []
        for a_data in assets_data:
            existing = Asset.query.filter_by(title=a_data["title"]).first()
            if not existing:
                asset = Asset(**a_data)
                db.session.add(asset)
                asset_objects.append(asset)
            else:
                asset_objects.append(existing)
        db.session.commit()
        print(f"  ✔ Assets seeded ({len(assets_data)} entries).")

        # ===================================================================
        # 4. TEST CASES
        # Realistic lab/POV test scenarios for ZTB validation.
        # ===================================================================
        test_cases_data = [
            {
                "title": "Branch Internet Breakout",
                "description": "Verify direct internet access from branch",
                "steps": (
                    "1. Configure ZTB policy\n"
                    "2. Test internet access from branch device\n"
                    "3. Verify traffic goes direct"
                ),
                "expected_result": "Traffic routes direct to internet without backhauling",
            },
            {
                "title": "Zero Trust App Access",
                "description": "Verify app access uses zero trust policies",
                "steps": (
                    "1. Attempt access to internal app\n"
                    "2. Verify ZT policy applied\n"
                    "3. Check logs"
                ),
                "expected_result": "Access granted only to authorized users/devices",
            },
            {
                "title": "MPLS Failover",
                "description": "Test failover from MPLS to broadband",
                "steps": (
                    "1. Simulate MPLS failure\n"
                    "2. Monitor traffic rerouting\n"
                    "3. Check application continuity"
                ),
                "expected_result": "Seamless failover within 30 seconds",
            },
            {
                "title": "Branch Security Policy",
                "description": "Verify security policies enforced at branch",
                "steps": (
                    "1. Attempt access to blocked site\n"
                    "2. Verify block page shown\n"
                    "3. Check policy logs"
                ),
                "expected_result": "Blocked traffic logged and user shown block page",
            },
            {
                "title": "SD-WAN Integration",
                "description": "Verify ZTB integrates with SD-WAN",
                "steps": (
                    "1. Configure SD-WAN integration\n"
                    "2. Test traffic steering\n"
                    "3. Verify ZT policies applied"
                ),
                "expected_result": "SD-WAN traffic subject to ZT security policies",
            },
        ]

        tc_objects = []
        for tc_data in test_cases_data:
            existing = TestCase.query.filter_by(title=tc_data["title"]).first()
            if not existing:
                tc = TestCase(**tc_data)
                db.session.add(tc)
                tc_objects.append(tc)
            else:
                tc_objects.append(existing)
        db.session.commit()
        print(f"  ✔ Test cases seeded ({len(test_cases_data)} entries).")

        # ===================================================================
        # 5. POV PLANNER
        # Week-by-week proof-of-value execution plan with owner and status.
        # ===================================================================
        pov_steps_data = [
            {
                "title": "Discovery & Scoping",
                "description": "Understand customer environment and requirements",
                "duration": "Week 1",
                "owner": "SE",
                "status": "Pending",
            },
            {
                "title": "Environment Setup",
                "description": "Deploy ZTB connectors and configure base policies",
                "duration": "Week 2",
                "owner": "SE + Customer IT",
                "status": "Pending",
            },
            {
                "title": "Use Case Validation",
                "description": "Test agreed use cases with customer team",
                "duration": "Week 3",
                "owner": "Customer IT",
                "status": "Pending",
            },
            {
                "title": "Executive Readout",
                "description": "Present POV results and business value to stakeholders",
                "duration": "Week 4",
                "owner": "SE + AE",
                "status": "Pending",
            },
            {
                "title": "Proposal & Next Steps",
                "description": "Deliver commercial proposal based on POV findings",
                "duration": "Week 4",
                "owner": "AE",
                "status": "Pending",
            },
        ]

        pov_objects = []
        for pov_data in pov_steps_data:
            existing = POVPlanner.query.filter_by(title=pov_data["title"]).first()
            if not existing:
                pov = POVPlanner(**pov_data)
                db.session.add(pov)
                pov_objects.append(pov)
            else:
                pov_objects.append(existing)
        db.session.commit()
        print(f"  ✔ POV planner steps seeded ({len(pov_steps_data)} entries).")
        # ===================================================================
        # 6. ROADBLOCKS
        # Common deal/technical obstacles with suggested mitigations.
        # severity: High = deal-stopper risk; Medium = manageable friction.
        # ===================================================================
        roadblocks_data = [
            {
                "title": "Budget Approval Pending",
                "description": "Customer needs finance sign-off",
                "category": "Commercial",
                "severity": "High",
                "mitigation": "Provide ROI analysis and executive business case",
            },
            {
                "title": "Existing MPLS Contract",
                "description": "Customer locked in MPLS contract for 18 months",
                "category": "Commercial",
                "severity": "Medium",
                "mitigation": "Plan phased migration starting with new sites",
            },
            {
                "title": "IT Resource Constraints",
                "description": "Customer IT team stretched thin",
                "category": "Technical",
                "severity": "Medium",
                "mitigation": "Offer professional services support for deployment",
            },
            {
                "title": "Security Team Approval",
                "description": "Security team needs to review ZT architecture",
                "category": "Technical",
                "severity": "High",
                "mitigation": "Schedule architecture review with security team",
            },
            {
                "title": "Competing Vendor Evaluation",
                "description": "Customer also evaluating competitor",
                "category": "Commercial",
                "severity": "High",
                "mitigation": "Accelerate POV and provide competitive differentiation",
            },
        ]

        for rb_data in roadblocks_data:
            existing = Roadblock.query.filter_by(title=rb_data["title"]).first()
            if not existing:
                db.session.add(Roadblock(**rb_data))
        db.session.commit()
        print(f"  ✔ Roadblocks seeded ({len(roadblocks_data)} entries).")

        # ===================================================================
        # 7. QUESTION CATEGORIES, QUESTIONS & OPTIONS
        # Discovery questionnaire grouped by topic.
        # options_type: "select_one" | "select_all" | "textbox"
        # Each option can link to value_prop, asset, test_case, pov_step IDs
        # so the engine can surface relevant content automatically.
        # ===================================================================

        # ------ helper: resolve FK ids from seeded objects ------
        # vp_objects  index: 0=MPLS Cost, 1=Simplified Net, 2=ZT Posture,
        #                    3=SD-WAN, 4=Unified Policy, 5=Cloud-First
        # asset_objects index: 0=Datasheet, 1=ROI Calc, 2=Demo Video,
        #                      3=Ref Arch, 4=TCO, 5=Case Study
        # tc_objects  index: 0=Breakout, 1=ZT App, 2=MPLS Failover,
        #                    3=Branch Sec, 4=SD-WAN
        # pov_objects index: 0=Discovery, 1=Env Setup, 2=UC Validation,
        #                    3=Exec Readout, 4=Proposal

        # Re-fetch to get DB-assigned IDs (safe after commit above)
        vps   = ValueProp.query.order_by(ValueProp.id).all()
        assets = Asset.query.order_by(Asset.id).all()
        tcs   = TestCase.query.order_by(TestCase.id).all()
        povs  = POVPlanner.query.order_by(POVPlanner.id).all()

        # ---------------------------------------------------------------
        # Category 1: Network Infrastructure
        # ---------------------------------------------------------------
        cat1 = QuestionCategory.query.filter_by(name="Network Infrastructure").first()
        if not cat1:
            cat1 = QuestionCategory(name="Network Infrastructure", order=1)
            db.session.add(cat1)
            db.session.commit()

        # Q1-1: How many branch locations?
        q1_1 = Question.query.filter_by(
            text="How many branch locations does your organization have?",
            category_id=cat1.id,
        ).first()
        if not q1_1:
            q1_1 = Question(
                text="How many branch locations does your organization have?",
                options_type="select_one",
                category_id=cat1.id,
                order=1,
                info_only=False,
            )
            db.session.add(q1_1)
            db.session.commit()
            # Options — link to MPLS Cost VP and Ref Arch asset
            for label in ["1-10", "11-50", "51-200", "200+"]:
                opt = QuestionOption(
                    question_id=q1_1.id,
                    label=label,
                    value_prop_id=vps[0].id if vps else None,   # Eliminate MPLS Costs
                    asset_id=assets[3].id if len(assets) > 3 else None,  # Ref Arch
                )
                db.session.add(opt)
            db.session.commit()

        # Q1-2: What WAN technology?
        q1_2 = Question.query.filter_by(
            text="What WAN technology are you currently using?",
            category_id=cat1.id,
        ).first()
        if not q1_2:
            q1_2 = Question(
                text="What WAN technology are you currently using?",
                options_type="select_all",
                category_id=cat1.id,
                order=2,
                info_only=False,
            )
            db.session.add(q1_2)
            db.session.commit()
            wan_opts = [
                # label,         vp_idx, asset_idx, tc_idx, pov_idx
                ("MPLS",            0,      4,       2,      0),  # MPLS Cost VP, TCO asset, MPLS Failover TC, Discovery POV
                ("Broadband/Internet", 0,   1,       0,      1),  # MPLS Cost VP, ROI Calc, Breakout TC, Env Setup
                ("SD-WAN",          3,      3,       4,      1),  # SD-WAN VP, Ref Arch, SD-WAN TC
                ("4G/LTE",          0,      1,       0,      0),
            ]
            for label, vi, ai, ti, pi in wan_opts:
                opt = QuestionOption(
                    question_id=q1_2.id,
                    label=label,
                    value_prop_id=vps[vi].id if len(vps) > vi else None,
                    asset_id=assets[ai].id if len(assets) > ai else None,
                    test_case_id=tcs[ti].id if len(tcs) > ti else None,
                    pov_step_id=povs[pi].id if len(povs) > pi else None,
                )
                db.session.add(opt)
            db.session.commit()

        # Q1-3: Primary challenge (textbox — no options)
        q1_3 = Question.query.filter_by(
            text="What is your primary challenge with current branch networking?",
            category_id=cat1.id,
        ).first()
        if not q1_3:
            q1_3 = Question(
                text="What is your primary challenge with current branch networking?",
                options_type="textbox",
                category_id=cat1.id,
                order=3,
                info_only=False,
            )
            db.session.add(q1_3)
            db.session.commit()

        print("  ✔ Question Category 1 (Network Infrastructure) seeded.")

        # ---------------------------------------------------------------
        # Category 2: Security Requirements
        # ---------------------------------------------------------------
        cat2 = QuestionCategory.query.filter_by(name="Security Requirements").first()
        if not cat2:
            cat2 = QuestionCategory(name="Security Requirements", order=2)
            db.session.add(cat2)
            db.session.commit()

        # Q2-1: Security solutions at branches
        q2_1 = Question.query.filter_by(
            text="What security solutions are deployed at branches today?",
            category_id=cat2.id,
        ).first()
        if not q2_1:
            q2_1 = Question(
                text="What security solutions are deployed at branches today?",
                options_type="select_all",
                category_id=cat2.id,
                order=1,
                info_only=False,
            )
            db.session.add(q2_1)
            db.session.commit()
            sec_opts = [
                # label,    vp_idx, asset_idx, tc_idx, pov_idx
                ("Firewall",       1,  3,  3,  1),  # Simplified Networking, Ref Arch, Branch Security TC
                ("IPS/IDS",        2,  3,  3,  1),  # ZT Posture, Ref Arch
                ("Web Proxy",      2,  0,  3,  1),  # ZT Posture, Datasheet
                ("None",           2,  5,  1,  0),  # ZT Posture, Case Study, ZT App TC
            ]
            for label, vi, ai, ti, pi in sec_opts:
                opt = QuestionOption(
                    question_id=q2_1.id,
                    label=label,
                    value_prop_id=vps[vi].id if len(vps) > vi else None,
                    asset_id=assets[ai].id if len(assets) > ai else None,
                    test_case_id=tcs[ti].id if len(tcs) > ti else None,
                    pov_step_id=povs[pi].id if len(povs) > pi else None,
                )
                db.session.add(opt)
            db.session.commit()

        # Q2-2: Importance of zero trust
        q2_2 = Question.query.filter_by(
            text="How important is zero trust security for your branch?",
            category_id=cat2.id,
        ).first()
        if not q2_2:
            q2_2 = Question(
                text="How important is zero trust security for your branch?",
                options_type="select_one",
                category_id=cat2.id,
                order=2,
                info_only=False,
            )
            db.session.add(q2_2)
            db.session.commit()
            for label in ["Critical", "Important", "Nice to have", "Not a priority"]:
                opt = QuestionOption(
                    question_id=q2_2.id,
                    label=label,
                    value_prop_id=vps[2].id if len(vps) > 2 else None,  # ZT Posture
                    asset_id=assets[0].id if assets else None,           # Datasheet
                    test_case_id=tcs[1].id if len(tcs) > 1 else None,   # ZT App Access
                )
                db.session.add(opt)
            db.session.commit()

        # Q2-3: Compliance requirements
        q2_3 = Question.query.filter_by(
            text="Do you have compliance requirements affecting branch security?",
            category_id=cat2.id,
        ).first()
        if not q2_3:
            q2_3 = Question(
                text="Do you have compliance requirements affecting branch security?",
                options_type="select_one",
                category_id=cat2.id,
                order=3,
                info_only=False,
            )
            db.session.add(q2_3)
            db.session.commit()
            for label in ["Yes - PCI", "Yes - HIPAA", "Yes - SOC2", "No specific compliance"]:
                opt = QuestionOption(
                    question_id=q2_3.id,
                    label=label,
                    value_prop_id=vps[2].id if len(vps) > 2 else None,  # ZT Posture
                    asset_id=assets[5].id if len(assets) > 5 else None, # Case Study
                )
                db.session.add(opt)
            db.session.commit()

        print("  ✔ Question Category 2 (Security Requirements) seeded.")

        # ---------------------------------------------------------------
        # Category 3: Business Priorities
        # ---------------------------------------------------------------
        cat3 = QuestionCategory.query.filter_by(name="Business Priorities").first()
        if not cat3:
            cat3 = QuestionCategory(name="Business Priorities", order=3)
            db.session.add(cat3)
            db.session.commit()

        # Q3-1: Primary motivation
        q3_1 = Question.query.filter_by(
            text="What is your primary motivation for evaluating ZTB?",
            category_id=cat3.id,
        ).first()
        if not q3_1:
            q3_1 = Question(
                text="What is your primary motivation for evaluating ZTB?",
                options_type="select_one",
                category_id=cat3.id,
                order=1,
                info_only=False,
            )
            db.session.add(q3_1)
            db.session.commit()
            motivation_opts = [
                # label,               vp_idx, asset_idx, tc_idx, pov_idx
                ("Cost Reduction",        0,      4,       2,      0),  # MPLS Cost, TCO, MPLS Failover
                ("Security Improvement",  2,      0,       1,      2),  # ZT Posture, Datasheet, ZT App
                ("Operational Simplicity",1,      2,       0,      1),  # Simplified Net, Demo, Breakout
                ("Cloud Adoption",        5,      3,       0,      1),  # Cloud-First, Ref Arch, Breakout
            ]
            for label, vi, ai, ti, pi in motivation_opts:
                opt = QuestionOption(
                    question_id=q3_1.id,
                    label=label,
                    value_prop_id=vps[vi].id if len(vps) > vi else None,
                    asset_id=assets[ai].id if len(assets) > ai else None,
                    test_case_id=tcs[ti].id if len(tcs) > ti else None,
                    pov_step_id=povs[pi].id if len(povs) > pi else None,
                )
                db.session.add(opt)
            db.session.commit()

        # Q3-2: Target timeline
        q3_2 = Question.query.filter_by(
            text="What is your target timeline for deployment?",
            category_id=cat3.id,
        ).first()
        if not q3_2:
            q3_2 = Question(
                text="What is your target timeline for deployment?",
                options_type="select_one",
                category_id=cat3.id,
                order=2,
                info_only=False,
            )
            db.session.add(q3_2)
            db.session.commit()
            timeline_opts = [
                ("0-3 months",   4,  1),   # Proposal POV step, ROI Calc asset
                ("3-6 months",   3,  1),   # Exec Readout POV
                ("6-12 months",  1,  3),   # Env Setup POV, Ref Arch
                ("12+ months",   0,  4),   # Discovery POV, TCO asset
            ]
            for label, pi, ai in timeline_opts:
                opt = QuestionOption(
                    question_id=q3_2.id,
                    label=label,
                    asset_id=assets[ai].id if len(assets) > ai else None,
                    pov_step_id=povs[pi].id if len(povs) > pi else None,
                )
                db.session.add(opt)
            db.session.commit()

        # Q3-3: Additional context (textbox)
        q3_3 = Question.query.filter_by(
            text="Any additional context about your requirements?",
            category_id=cat3.id,
        ).first()
        if not q3_3:
            q3_3 = Question(
                text="Any additional context about your requirements?",
                options_type="textbox",
                category_id=cat3.id,
                order=3,
                info_only=False,
            )
            db.session.add(q3_3)
            db.session.commit()

        print("  ✔ Question Category 3 (Business Priorities) seeded.")
        # ===================================================================
        # 8. ASSESSMENT CONFIG
        # Marks every question as active and assigns a display_order that
        # mirrors the category → question ordering used above.
        # One config row per question ensures the assessment engine knows
        # which questions to include and in what sequence.
        # ===================================================================
        all_questions = Question.query.order_by(
            Question.category_id, Question.order
        ).all()

        display_order = 1
        for question in all_questions:
            existing_cfg = AssessmentConfig.query.filter_by(
                question_id=question.id
            ).first()
            if not existing_cfg:
                cfg = AssessmentConfig(
                    question_id=question.id,
                    is_active=True,
                    display_order=display_order,
                )
                db.session.add(cfg)
            display_order += 1

        db.session.commit()
        print(
            f"  ✔ Assessment config seeded "
            f"({len(all_questions)} active question entries)."
        )

        # ===================================================================
        # Done
        # ===================================================================
        print()
        print("\u2705 Sample data initialized successfully!")


# ---------------------------------------------------------------------------
# MAIN BLOCK
# Run directly: python init_sample_data.py
# Must be executed AFTER init_db.py has created all tables.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== ZTB Super App — Sample Data Initialisation ===")
    print()
    main()
