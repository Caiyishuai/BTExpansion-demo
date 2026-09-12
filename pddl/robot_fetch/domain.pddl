(define (domain robot-fetch)
  (:requirements :strips :typing :negative-preconditions)

  (:types
    location object - thing
    item - object
  )

  (:predicates
    (robot-at ?l - location)
    (item-at ?i - item ?l - location)
    (holding ?i - item)
    (hand-empty)
    (reachable ?l - location)
  )

  (:action move
    :parameters (?from - location ?to - location)
    :precondition (and (robot-at ?from) (reachable ?to))
    :effect (and (robot-at ?to) (not (robot-at ?from)))
    :cost 2
  )

  (:action pick
    :parameters (?i - item ?l - location)
    :precondition (and (robot-at ?l) (item-at ?i ?l) (hand-empty))
    :effect (and (holding ?i) (not (item-at ?i ?l)) (not (hand-empty)))
    :cost 1
  )

  (:action place
    :parameters (?i - item ?l - location)
    :precondition (and (robot-at ?l) (holding ?i))
    :effect (and (item-at ?i ?l) (hand-empty) (not (holding ?i)))
    :cost 1
  )
)
