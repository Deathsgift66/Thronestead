from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from backend.database import Base
from backend.models import Alliance, AllianceVote, AllianceVoteParticipant, User
from backend.routers.alliance_votes import (
    BallotPayload,
    VoteProposal,
    cast_ballot,
    propose_vote,
    vote_results,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def seed_user(db):
    db.add(Alliance(alliance_id=1, name="A"))
    user = User(user_id="u1", username="u", email="u@test.com", alliance_id=1)
    db.add(user)
    db.commit()
    return "u1"


def test_propose_vote_creates_record():
    Session = setup_db()
    db = Session()
    uid = seed_user(db)

    res = propose_vote(
        VoteProposal(proposal_type="test", proposal_details={"a": 1}),
        user_id=uid,
        db=db,
    )
    vote = db.query(AllianceVote).first()
    assert vote and vote.proposal_type == "test"
    assert res["vote_id"] == vote.vote_id


def test_cast_ballot_records_choice():
    Session = setup_db()
    db = Session()
    uid = seed_user(db)
    vote_id = propose_vote(
        VoteProposal(proposal_type="x", proposal_details={}), user_id=uid, db=db
    )["vote_id"]

    cast_ballot(BallotPayload(vote_id=vote_id, choice="yes"), user_id=uid, db=db)
    part = (
        db.query(AllianceVoteParticipant)
        .filter_by(vote_id=vote_id, user_id=uid)
        .first()
    )
    assert part and part.vote_choice == "yes"


def test_vote_results_counts_votes():
    Session = setup_db()
    db = Session()
    uid = seed_user(db)
    vote_id = propose_vote(
        VoteProposal(proposal_type="y", proposal_details={}), user_id=uid, db=db
    )["vote_id"]
    cast_ballot(BallotPayload(vote_id=vote_id, choice="yes"), user_id=uid, db=db)

    res = vote_results(vote_id=vote_id, user_id=uid, db=db)
    assert res["results"].get("yes") == 1 and res["total"] == 1


def test_non_member_cannot_vote():
    Session = setup_db()
    db = Session()
    uid = seed_user(db)
    vote_id = propose_vote(
        VoteProposal(proposal_type="z", proposal_details={}), user_id=uid, db=db
    )["vote_id"]
    db.add(User(user_id="u2", username="b", email="b@test.com"))
    db.commit()
    try:
        cast_ballot(BallotPayload(vote_id=vote_id, choice="no"), user_id="u2", db=db)
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        assert False
