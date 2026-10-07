use super::*;
use rx_domain::canonical;

#[test]
fn runtime_skill_catalog_is_read_only_and_is_not_start_authority() {
    let mut f = fixture_with_process(1, false, false, true, Some(TestProcess::Branch));
    let before = f
        .app
        .inspect_cell(&f.operator, &f.configuration.id)
        .unwrap();
    let catalog = f.app.runtime_skill_catalog(&f.operator).unwrap();
    assert_eq!(catalog.bindings.len(), 1);
    assert_eq!(
        catalog.bindings[0].binding.name,
        f.configuration.process.as_ref().unwrap().process
    );
    assert_eq!(
        catalog.bindings[0].binding.input_mode,
        "BOUND_CONFIGURATION"
    );
    assert_eq!(
        catalog.bindings[0].commissioning,
        Some(Commissioning::NotCommissioned)
    );
    let after = f
        .app
        .inspect_cell(&f.operator, &f.configuration.id)
        .unwrap();
    assert_eq!(
        canonical::bytes(&before).unwrap(),
        canonical::bytes(&after).unwrap()
    );
    let run = f
        .app
        .create_run(&f.operator, id().as_str(), create_command(&f, after.0))
        .unwrap();
    assert!(
        f.app
            .start_run(
                &f.operator,
                id().as_str(),
                start_command(&f, &run, after.0, 1)
            )
            .is_err()
    );
    let result = f.app.runtime_skill_result(&f.operator, &run.id).unwrap();
    assert_eq!(result.result_owner, "PLATFORM");
    assert_eq!(result.run.value.state, RunState::Prepared);
    assert!(result.parts.is_empty() && result.work.is_empty());
    assert!(result.current_binding_matches);
    assert_eq!(
        result.binding.binding_digest,
        catalog.bindings[0].binding.binding_digest
    );
}

#[test]
fn runtime_skill_reads_follow_current_principal_scope_and_preserve_run_identity() {
    let mut f = fixture_with_process(1, true, false, true, Some(TestProcess::Branch));
    let catalog = f.app.runtime_skill_catalog(&f.operator).unwrap();
    let revision = f
        .app
        .inspect_cell(&f.operator, &f.configuration.id)
        .unwrap()
        .0;
    let run = f
        .app
        .create_run(&f.operator, id().as_str(), create_command(&f, revision))
        .unwrap();
    let view = f.app.runtime_skill_result(&f.operator, &run.id).unwrap();
    assert_eq!(view.run.value.id, run.id);
    assert_eq!(view.binding.recipe.sha256, run.recipe_digest);
    assert_eq!(
        view.binding.binding_digest,
        catalog.bindings[0].binding.binding_digest
    );
    let mut changed = principal("operator", &[Role::Operator]);
    changed.cells.clear();
    f.app
        .put_principal(&f.admin, changed, Some(Counter(1)))
        .unwrap();
    assert!(
        f.app
            .runtime_skill_catalog(&f.operator)
            .unwrap()
            .bindings
            .is_empty()
    );
    assert!(f.app.runtime_skill_result(&f.operator, &run.id).is_err());
}

fn admitted_process_work() -> (Fixture, Work) {
    let mut f = fixture_with_peer(1, true, false, true, Some(TestProcess::Branch), true);
    let run = start(&mut f, 1);
    let part = f
        .app
        .begin_part(
            &f.executor,
            id().as_str(),
            &run.id,
            run.budget.as_ref().unwrap().revision(),
        )
        .unwrap();
    report_select(&mut f, true);
    let branch = f.configuration.process.as_ref().unwrap().root.id.clone();
    let revision = f.app.inspect_run(&f.executor, &run.id).unwrap().0;
    f.app
        .choose_process_branch(
            &f.executor,
            id().as_str(),
            &run.id,
            &branch,
            part.ordinal,
            revision,
        )
        .unwrap();
    let progress = f
        .app
        .process_progress(&f.executor, &run.id, part.ordinal)
        .unwrap();
    let activation = f
        .app
        .resolve_activation(
            &f.executor,
            &run.id,
            &progress.frontier.operations[0],
            part.ordinal,
            progress.run_revision,
        )
        .unwrap();
    let work = submit(&mut f, &activation, id().as_str()).unwrap();
    (f, work)
}

fn capture_process_work(f: &mut Fixture, work: &Work, status: i64) -> NativeEvidence {
    let invocation = id();
    let operation = work.operation.id();
    for (delivery, sequence, state) in [
        (operation.clone(), 10, ReceiptState::Prepared),
        (
            rx_application::engine::authorization_delivery_id(operation),
            11,
            ReceiptState::ResultCaptured,
        ),
    ] {
        assert!(f.app.begin_delivery(&delivery).unwrap());
        f.app
            .record_host_receipt(
                &f.hosts[0],
                &delivery,
                HostReceipt {
                    operation: operation.clone(),
                    digest: work.intent.digest().unwrap(),
                    invocation: Some(invocation.clone()),
                    journal: f.registrations[0].delivery_journal.clone(),
                    sequence: Counter(sequence),
                    state,
                },
            )
            .unwrap();
    }
    let evidence = NativeEvidence {
        id: id(),
        operation: operation.clone(),
        invocation,
        profile_digest: work.intent.profile_digest,
        device_session: id(),
        status_schema: name("rx.sim.completed.v1"),
        status: Integer(status),
        captured_at: expiry(1000),
        native_details: Some(NativeEvidenceDetails {
            native_id: Some("private-provider-result".into()),
            native_data: Some(artifact(66, "private/provider-data.v1")),
        }),
    };
    f.app
        .ingest_evidence(
            &f.hosts[0],
            EvidenceBatch {
                journal: id(),
                first: Counter(1),
                records: vec![evidence.clone()],
            },
        )
        .unwrap();
    evidence
}

#[test]
fn runtime_skill_native_result_exposes_referenced_status_without_private_details_or_writes() {
    for (status, outcome) in [
        (0, rx_domain::operation::Outcome::Succeeded),
        (1, rx_domain::operation::Outcome::Failed),
    ] {
        let (mut f, work) = admitted_process_work();
        let evidence = capture_process_work(&mut f, &work, status);
        let before = f
            .app
            .inspect_work(&f.operator, work.operation.id())
            .unwrap();
        let result = f.app.runtime_skill_result(&f.operator, &work.run).unwrap();
        let observed = &result.work[0];
        assert_eq!(observed.operation.outcome(), outcome);
        assert_eq!(observed.native_results.len(), 1);
        let native = &observed.native_results[0];
        assert_eq!(native.evidence, evidence.id);
        assert_eq!(native.invocation, evidence.invocation);
        assert_eq!(native.status_schema, evidence.status_schema);
        assert_eq!(native.status, evidence.status);
        assert_eq!(native.captured_at, evidence.captured_at);
        let serialized = serde_json::to_value(native).unwrap();
        assert_eq!(
            serialized
                .as_object()
                .unwrap()
                .keys()
                .map(String::as_str)
                .collect::<BTreeSet<_>>(),
            BTreeSet::from([
                "captured_at",
                "evidence",
                "invocation",
                "status",
                "status_schema",
            ])
        );
        assert!(
            !String::from_utf8(canonical::bytes(&result).unwrap())
                .unwrap()
                .contains("private-provider-result")
        );
        assert!(
            f.app
                .inspect_native_evidence(&f.operator, &evidence.id)
                .is_err(),
            "the projection must not grant access to full native details"
        );
        let after = f
            .app
            .inspect_work(&f.operator, work.operation.id())
            .unwrap();
        assert_eq!(
            canonical::bytes(&before).unwrap(),
            canonical::bytes(&after).unwrap()
        );
    }
}

#[test]
fn runtime_skill_non_native_not_executed_proof_does_not_invent_a_native_result() {
    let (mut f, work) = admitted_process_work();
    f.app.hold(&f.operator, id().as_str(), &work.cell).unwrap();
    let result = f.app.runtime_skill_result(&f.operator, &work.run).unwrap();
    assert_eq!(
        result.work[0].operation.outcome(),
        rx_domain::operation::Outcome::NotExecuted
    );
    assert!(!result.work[0].operation.evidence_ids().is_empty());
    assert!(result.work[0].native_results.is_empty());
}

#[test]
fn runtime_skill_native_result_refuses_mismatched_stored_referenced_evidence() {
    use rx_application::persistence::{doc, key};
    for field in ["id", "operation", "invocation", "profile"] {
        let (mut f, work) = admitted_process_work();
        let evidence = capture_process_work(&mut f, &work, 0);
        let original_key = key("evidence", &evidence.id);
        let mut corrupted = evidence.clone();
        match field {
            "id" => corrupted.id = id(),
            "operation" => corrupted.operation = id(),
            "invocation" => corrupted.invocation = id(),
            "profile" => corrupted.profile_digest = Digest::from_bytes([99; 32]),
            _ => unreachable!(),
        }
        let installation = f.app.installation.id.clone();
        let mut repository = f.app.into_repository();
        // Deliberate test-only storage corruption after real receipt/evidence ingestion.
        // The original Operation still references the same evidence key; it is not an
        // unrelated row that the projection could safely ignore.
        repository
            .transact(|tx| {
                let original = tx.get(&original_key)?.unwrap();
                tx.put(
                    &original_key,
                    Some(original.revision),
                    &doc("rx.internal.native-evidence.v1", &corrupted)?,
                )?;
                Ok(())
            })
            .unwrap();
        f.app = Engine::open(
            repository,
            f.clock.clone(),
            SimulationAuthority,
            installation,
            principal("admin", &[Role::AccountAdmin]),
        )
        .unwrap();
        f.operator.session = f
            .app
            .authenticated_terminal_user_session(
                &f.operator.principal,
                id(),
                Counter(99_000),
                Digest::from_bytes([77; 32]),
            )
            .unwrap()
            .id;
        assert!(matches!(
            f.app.runtime_skill_result(&f.operator, &work.run),
            Err(StoreError::Integrity(message))
                if message == "skill native result correlation differs"
        ));
    }
}
