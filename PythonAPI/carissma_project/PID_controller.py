class PID:
	"""
	Discrete PID control
	"""

	def __init__(self, P=2.0, I=0.0, D=1.0, Derivator=0, Integrator=0, Integrator_windup_max=100, Integrator_windup_min=-100):

		self.Kp=P
		self.Ki=I
		self.Kd=D
		self.Derivator=Derivator
		self.Integrator=Integrator
		self.Integrator_max=Integrator_windup_max
		self.Integrator_min=Integrator_windup_min

		self.set_point=0.0
		self.error=0.0

	def update(self,current_value):
		"""
		Calculate PID output value for given reference input and feedback
		"""

		self.error = self.set_point - current_value # vel_setpoint - vel_atual

		self.P_value = self.Kp * self.error
		self.D_value = self.Kd * ( self.error - self.Derivator)
		self.Derivator = self.error

		self.Integrator = self.Integrator + self.error

		if self.Integrator > self.Integrator_max:
			self.Integrator = self.Integrator_max
		elif self.Integrator < self.Integrator_min:
			self.Integrator = self.Integrator_min

		self.I_value = self.Integrator * self.Ki

		PID = self.P_value + self.I_value + self.D_value

		return PID

	def setPoint(self,set_point):
		"""
		Initilize the setpoint of PID
		"""
		self.set_point = set_point
		self.Integrator=0
		self.Derivator=0

	def getSetPoint(self):
		return self.set_point

	def getError(self):
		self.set_point = 1e-6 if self.set_point == 0 else self.set_point
		error_percentage = (self.error/self.set_point)*100
		return error_percentage

	def getIntegrator(self):
		return self.Integrator

	def getDerivator(self):
		return self.Derivator

	def setWindup(self, windup_max, windup_min):
		self.Integrator_max = windup_max
		self.Integrator_min = windup_min