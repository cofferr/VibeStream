import React, { useMemo } from 'react';
import { useForm } from 'react-hook-form';
import Button from '@/components/ui/button';
import Input from '@/components/ui/input';
import Label from '@/components/ui/label';
import Spinner from '@/components/ui/spinner';
import { CardTitle, CardDescription, CardFooter } from '@/components/ui/card';

const RegisterForm = ({ onSubmit, error, loading }) => {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm();

  const watchPassword = watch("password", "");
  const watchBirthdate = watch("birthdate", "");

  // Validaciones de fecha mejoradas
  const dateValidations = useMemo(() => {
    const validations = {
      required: "Fecha de nacimiento es requerida",
    };

    if (watchBirthdate) {
      validations.validate = {
        futureDate: (value) => {
          const selectedDate = new Date(value);
          const today = new Date();
          today.setHours(0, 0, 0, 0); // Normalizar a inicio del día
          return selectedDate <= today || "La fecha no puede ser en el futuro";
        },
        minimumAge: (value) => {
          const selectedDate = new Date(value);
          const today = new Date();
          let age = today.getFullYear() - selectedDate.getFullYear();
          const monthDiff = today.getMonth() - selectedDate.getMonth();
          
          // Ajustar edad si el cumpleaños aún no ha llegado este año
          if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < selectedDate.getDate())) {
            age--;
          }
          return age >= 13 || "Debes tener al menos 13 años para registrarte";
        },
        maximumAge: (value) => {
          const selectedDate = new Date(value);
          const today = new Date();
          let age = today.getFullYear() - selectedDate.getFullYear();
          const monthDiff = today.getMonth() - selectedDate.getMonth();
          
          if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < selectedDate.getDate())) {
            age--;
          }
          return age <= 120 || "Por favor verifica tu fecha de nacimiento";
        },
        validDate: (value) => {
          const selectedDate = new Date(value);
          return !isNaN(selectedDate.getTime()) || "Fecha inválida";
        }
      };
    }

    return validations;
  }, [watchBirthdate]);

  // Validaciones de username mejoradas
  const usernameValidations = {
    required: "Username es requerido",
    minLength: {
      value: 3,
      message: "El username debe tener al menos 3 caracteres"
    },
    maxLength: {
      value: 20,
      message: "El username no puede tener más de 20 caracteres"
    },
    pattern: {
      value: /^[a-zA-Z0-9_]+$/,
      message: "Solo se permiten letras, números y guiones bajos"
    }
  };

  // Validaciones de email mejoradas
  const emailValidations = {
    required: "Email es requerido",
    pattern: {
      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
      message: "Email inválido"
    }
  };

  // Validaciones de password mejoradas
  const passwordValidations = {
    required: "Password es requerido",
    minLength: {
      value: 8,
      message: "La contraseña debe tener al menos 8 caracteres"
    },
    pattern: {
      value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      message: "Debe incluir mayúsculas, minúsculas y números"
    }
  };

  // Calcular edad para mostrar feedback útil
  const calculateAge = (birthdate) => {
    if (!birthdate) return null;
    
    const selectedDate = new Date(birthdate);
    const today = new Date();
    let age = today.getFullYear() - selectedDate.getFullYear();
    const monthDiff = today.getMonth() - selectedDate.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < selectedDate.getDate())) {
      age--;
    }
    
    return age;
  };

  const currentAge = watchBirthdate ? calculateAge(watchBirthdate) : null;

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div className="space-y-4">
        <CardTitle className="text-center text-2xl">Crear Cuenta</CardTitle>
        <CardDescription className="text-center">Unete a VibeStream — Es Gratis!</CardDescription>

        {/* Error general del formulario */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600 text-center">{error}</p>
          </div>
        )}

        <div>
          <Label htmlFor="reg-username">Username</Label>
          <Input 
            id="reg-username" 
            placeholder="tu_usuario"
            {...register("username", usernameValidations)} 
            className="mt-1" 
            error={errors.username}
          />
          {errors.username ? (
            <p className="text-xs text-red-500 mt-1">{errors.username.message}</p>
          ) : (
            <p className="text-xs text-gray-500 mt-1">3-20 caracteres, solo letras, números y _</p>
          )}
        </div>

        <div>
          <Label htmlFor="reg-email">Email</Label>
          <Input 
            id="reg-email" 
            type="email" 
            placeholder="tu@email.com"
            {...register("email", emailValidations)} 
            className="mt-1" 
            error={errors.email}
          />
          {errors.email && (
            <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>
          )}
        </div>

        <div>
          <Label htmlFor="reg-birthdate">Fecha de Nacimiento</Label>
          <Input 
            id="reg-birthdate" 
            type="date" 
            {...register("birthdate", dateValidations)} 
            className="mt-1" 
            error={errors.birthdate}
            max={new Date().toISOString().split('T')[0]} // Bloquear fechas futuras en el input
          />
          {errors.birthdate ? (
            <p className="text-xs text-red-500 mt-1">{errors.birthdate.message}</p>
          ) : currentAge !== null ? (
            <p className="text-xs text-green-600 mt-1">
              ✅ Edad válida: {currentAge} años
            </p>
          ) : (
            <p className="text-xs text-gray-500 mt-1">Debes tener al menos 13 años</p>
          )}
        </div>

        <div>
          <Label htmlFor="reg-password">Contraseña</Label>
          <Input
            id="reg-password"
            type="password"
            placeholder="••••••••"
            {...register("password", passwordValidations)}
            className="mt-1"
            error={errors.password}
          />
          {errors.password ? (
            <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>
          ) : (
            <p className="text-xs text-gray-500 mt-1">
              Mínimo 8 caracteres con mayúsculas, minúsculas y números
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="reg-confirm">Confirmar Contraseña</Label>
          <Input 
            id="reg-confirm" 
            type="password" 
            placeholder="••••••••"
            {...register("confirmPassword", { 
              required: "Confirma tu contraseña",
              validate: value => 
                value === watchPassword || "Las contraseñas no coinciden"
            })} 
            className="mt-1" 
            error={errors.confirmPassword}
          />
          {errors.confirmPassword && (
            <p className="text-xs text-red-500 mt-1">{errors.confirmPassword.message}</p>
          )}
        </div>
      </div>

      <CardFooter className="flex flex-col space-y-3 pt-4">
        <Button 
          type="submit" 
          variant="gradient" 
          className="w-full" 
          disabled={loading}
        >
          {loading ? <Spinner /> : "Crear Cuenta"}
        </Button>
        
        <p className="text-xs text-center text-gray-500">
          Al registrarte, aceptas nuestros{' '}
          <a href="/terms" className="text-indigo-600 hover:underline">
            Términos de Servicio
          </a>{' '}
          y{' '}
          <a href="/privacy" className="text-indigo-600 hover:underline">
            Política de Privacidad
          </a>
        </p>
      </CardFooter>
    </form>
  );
};

export default RegisterForm;