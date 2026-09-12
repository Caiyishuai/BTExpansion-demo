(define (domain unsupported-showcase)
  (:requirements :strips :typing :conditional-effects
                 :disjunctive-preconditions :fluents)

  (:types location item)

  (:predicates
    (at ?l - location)
    (holding ?i - item)
    (fragile ?i - item)
    (broken ?i - item)
    (clear ?l - location)
  )

  (:functions (battery) (weight ?i - item))

  (:action pick-conditional
    :parameters (?i - item ?l - location)
    :precondition (and (at ?l) (clear ?l))
    :effect (and (holding ?i)
                 (when (fragile ?i) (broken ?i)))
    :cost 1
  )

  (:action move-disjunctive
    :parameters (?from - location ?to - location)
    :precondition (or (at ?from) (clear ?to))
    :effect (and (at ?to) (not (at ?from)))
    :cost 1
  )

  (:action drain-numeric
    :parameters (?l - location)
    :precondition (and (at ?l) (> (battery) 10))
    :effect (and (clear ?l) (decrease (battery) 5))
    :cost 1
  )

  (:action universal-clear
    :parameters (?l - location)
    :precondition (forall (?i - item) (not (holding ?i)))
    :effect (clear ?l)
    :cost 1
  )

  (:action pre-add-overlap
    :parameters (?l - location)
    :precondition (and (at ?l) (clear ?l))
    :effect (and (clear ?l) (at ?l))
    :cost 1
  )
)
