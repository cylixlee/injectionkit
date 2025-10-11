from collections.abc import Callable, Iterable
from typing import Generic, TypeVar, final

from ._option import InvalidProviderFactoryError, Provider, Supplier
from .reflect import ConcreteType, Parameter, ParameterKind, Unspecified, signatureof, typeof

__all__ = ["Instantiator", "MissingDependencyError", "DependencyContainer"]


class Instantiator(object):
    """Coordinate argument binding for a provider factory.

    The helper inspects a factory callable once, records its signature, tracks default values, and assembles arguments
    over time before materializing the final instance when requested.

    Args:
        factory: Callable used to produce dependency instances.
    """

    _factory: Callable[..., object]
    _parameters: dict[str, Parameter]
    _arguments: dict[str, object]

    def __init__(self, factory: Callable[..., object]) -> None:
        """Pre-compute the signature and initialize argument slots.

        The constructor reflects the factory to discover every parameter, records metadata for quick lookups, and seeds
        an argument map with either default values or placeholders so that missing inputs can be detected before
        invocation.

        Args:
            factory: Callable responsible for constructing the target object.

        Returns:
            None
        """
        self._factory = factory
        self._parameters = {}
        self._arguments = {}

        signature = signatureof(factory)
        for parameter in signature.parameters:
            self._parameters[parameter.name] = parameter
            if parameter.default_value is not None:
                self._arguments[parameter.name] = parameter.default_value
            else:
                self._arguments[parameter.name] = Unspecified

    def argument(self, name: str, value: object) -> None:
        """Assign a concrete value to a named parameter.

        The method validates that the parameter exists, checks that the argument has not already been provided, and then
        captures the value so the factory call can later execute with a complete set of inputs.

        Args:
            name: Name of the parameter declared on the factory callable.
            value: Runtime object that should be passed when invoking the factory.

        Returns:
            None

        Raises:
            AttributeError: If the parameter is unknown or already assigned.
        """
        if name not in self._arguments:
            raise AttributeError(f"Unknown parameter: {name}")
        if self._arguments[name] is not Unspecified:
            raise AttributeError(f"Parameter already set: {name}")
        self._arguments[name] = value

    def instantiate(self) -> object:
        """Invoke the factory with the accumulated arguments.

        The instantiator builds positional and keyword argument collections from its internal buffer, verifies that
        every required parameter has a concrete value, and delegates to the stored factory to create the dependency
        instance.

        Returns:
            Object produced by the underlying factory callable.

        Raises:
            AttributeError: If any required parameter remains unset.
        """
        args = []
        kwargs = {}
        for name, argument in self._arguments.items():
            if argument is Unspecified:
                raise AttributeError(f"Parameter not set: {name}")
            parameter = self._parameters[name]
            if parameter.kind == ParameterKind.positional:
                args.append(argument)
            else:
                kwargs[name] = argument
        return self._factory(*args, **kwargs)


_T = TypeVar("_T")


class _Labeled(Generic[_T]):
    value: _T
    labels: set[str]

    def __init__(self, value: _T, labels: Iterable[str]) -> None:
        self.value = value
        self.labels = set(labels)

    def __contains__(self, labels: Iterable[str]) -> bool:
        if not labels:
            return not self.labels
        return self.labels.issuperset(labels)


class MissingDependencyError(Exception):
    """Report that dependency resolution failed for a concrete type.

    The exception is raised when the container exhausts both suppliers and providers without finding a candidate that
    matches the requested concrete type and labels.

    Attributes:
        concrete: Concrete type description used during the lookup.
        labels: Labels that scoped the resolution request.
    """

    concrete: ConcreteType
    labels: set[str]

    def __init__(self, concrete: ConcreteType, labels: set[str]) -> None:
        super().__init__(f"Missing dependency for `{concrete}`, labels: `{labels}`")
        self.concrete = concrete
        self.labels = labels


@final
class DependencyContainer(object):
    """Central registry for dependency providers and suppliers.

    The container maintains mappings from concrete types to provider factories or pre-built instances, resolves
    dependencies on demand, and enforces label matching when multiple variants are registered.
    """

    _providers: dict[ConcreteType, list[_Labeled[Provider]]]
    _instances: dict[ConcreteType, list[_Labeled[object]]]

    def __init__(self) -> None:
        """Prepare internal storage for providers and cached instances.

        Initialization creates dictionaries for provider factories and supplier-backed instances so subsequent
        registrations and resolutions operate on fresh state.

        Returns:
            None
        """
        self._providers = {}
        self._instances = {}

    def register(self, option: Provider | Supplier) -> None:
        """Register a provider or supplier for later resolution.

        The container distinguishes between eager instances and deferred factories, stores each under the appropriate
        concrete type, and tracks labels for quick retrieval during resolution.

        Args:
            option: Provider or supplier describing how to construct or supply a dependency.

        Returns:
            None
        """
        if isinstance(option, Provider):
            if option.concrete_type not in self._providers:
                self._providers[option.concrete_type] = [_Labeled(option, option.labels)]
            else:
                self._providers[option.concrete_type].append(_Labeled(option, option.labels))
        else:  # Supplier
            if option.concrete_type not in self._instances:
                self._instances[option.concrete_type] = [_Labeled(option.instance, option.labels)]
            else:
                self._instances[option.concrete_type].append(_Labeled(option.instance, option.labels))

    def resolve(self, annotation: object) -> object | list[object]:
        """Resolve a dependency from a type annotation.

        The annotation is reflected into a concrete type and label set, and the method produces either a single object
        or a collection of matches depending on the registration state.

        Args:
            annotation: Type annotation passed from consumer or provider signatures.

        Returns:
            Object or list of objects that satisfy the annotation.

        Raises:
            MissingDependencyError: If no matching provider or supplier is registered.
        """
        typ = typeof(annotation)
        return self.instantiate(typ.concrete, typ.labels)

    def instantiate(self, concrete: ConcreteType, labels: set[str]) -> object | list[object]:
        """Resolve a concrete type by combining suppliers and providers.

        Candidates include supplier instances that satisfy the label set and lazily evaluated providers; an error is
        raised when no option can produce the dependency.

        Args:
            concrete: Concrete type descriptor targeted for resolution.
            labels: Labels constraining the resolution scope.

        Returns:
            Single instance when exactly one candidate exists; otherwise, a list of all matching instances.

        Raises:
            InvalidProviderFactoryError: If a provider exposes a non-callable factory.
            MissingDependencyError: If no candidates satisfy the request.
        """
        candidates: list[object] = []
        if concrete in self._instances:
            for labeled_instance in self._instances[concrete]:
                if labels in labeled_instance:
                    candidates.append(labeled_instance.value)
        if concrete in self._providers:
            providers: list[Provider] = []
            for labeled_provider in self._providers[concrete]:
                if labels in labeled_provider:
                    providers.append(labeled_provider.value)
            for provider in providers:
                if not callable(provider.factory):
                    raise InvalidProviderFactoryError(provider.factory)
                signature = signatureof(provider.factory)
                instantiator = Instantiator(provider.factory)
                for parameter in signature.parameters:
                    try:
                        argument = self.instantiate(parameter.typ.concrete, parameter.typ.labels)
                        instantiator.argument(parameter.name, argument)
                    except MissingDependencyError:
                        if parameter.default_value is Unspecified:
                            raise
                candidates.append(instantiator.instantiate())
        if not candidates:
            if concrete.constructor is list and len(concrete.parameters) == 1:
                inner_type = concrete.parameters[0]
                inner_candidates = self.instantiate(inner_type, labels)
                if isinstance(inner_candidates, list):
                    return inner_candidates  # pyright: ignore[reportUnknownVariableType]
            raise MissingDependencyError(concrete, labels)
        if len(candidates) == 1:
            return candidates[0]
        return candidates
