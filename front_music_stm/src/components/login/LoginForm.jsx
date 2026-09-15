import React from 'react';
import { useForm } from 'react-hook-form';
import Button from '@/components/ui/button';
import Input from '@/components/ui/input';
import Label from '@/components/ui/label';
import Spinner from '@/components/ui/spinner';
import { CardTitle, CardDescription, CardFooter } from '@/components/ui/card';

const LoginForm = ({ onSubmit, error, loading }) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm();

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div className="space-y-4">
        <CardTitle className="text-center text-2xl">¡Bienvenido de nuevo!</CardTitle>
        <CardDescription className="text-center">Inicia sesión para continuar</CardDescription>

        {/* Error general del formulario */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600 text-center">{error}</p>
          </div>
        )}

        <div>
          <Label htmlFor="login-email">Email o Username</Label>
          <Input
            id="login-email"
            type="text"
            placeholder="tu@email.com o tu_usuario"
            {...register("email", { 
              required: "Email o username es requerido"
            })}
            className="mt-1"
            error={errors.email}
          />
          {errors.email && (
            <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>
          )}
        </div>

        <div>
          <Label htmlFor="login-password">Contraseña</Label>
          <Input
            id="login-password"
            type="password"
            placeholder="••••••••"
            {...register("password", { 
              required: "Contraseña es requerida"
            })}
            className="mt-1"
            error={errors.password}
          />
          {errors.password && (
            <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>
          )}
        </div>

        <div className="text-right">
          <a 
            href="/forgot-password" 
            className="text-sm text-indigo-600 hover:text-indigo-500 hover:underline"
          >
            ¿Olvidaste tu contraseña?
          </a>
        </div>
      </div>

      <CardFooter className="flex flex-col space-y-3 pt-4">
        <Button 
          type="submit" 
          variant="gradient" 
          className="w-full" 
          disabled={loading}
        >
          {loading ? <Spinner /> : "Iniciar Sesión"}
        </Button>
        
        <p className="text-xs text-center text-gray-500">
          ¿Problemas para iniciar sesión?{' '}
          <a href="/support" className="text-indigo-600 hover:underline">
            Contactar soporte
          </a>
        </p>
      </CardFooter>
    </form>
  );
};

export default LoginForm;